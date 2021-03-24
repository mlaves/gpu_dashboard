import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
from multiprocessing.connection import Listener
from multiprocessing import Process, Queue
from multiprocessing.connection import Connection
from collections import OrderedDict
from collections import deque


app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

num_hosts = 25
queue = Queue(maxsize=num_hosts)  # thread safe data structure
data_deq = deque(maxlen=num_hosts)

@app.callback(
    Output('live-graph', 'figure'),
    [Input('graph-update', 'n_intervals')]
)
def update_graph(n):
    global data_deq

    while not queue.empty():
        hostname, gpurel = queue.get()
        data_deq.append((hostname, gpurel))

    data_to_plot = {}
    for hostname, gpurel in data_deq:
        data_to_plot[hostname] = gpurel

    data_to_plot = OrderedDict(sorted(data_to_plot.items()))

    data = plotly.graph_objs.Bar(
        x=list(data_to_plot.keys()),
        y=list(data_to_plot.values()),
        name='GPU utilization')

    return {'data': [data],
            'layout': {
                'xaxis': dict(title='hosts'),
                'yaxis': dict(title='GPU memory usage [%]', range=[0, 100])
            }}


def connection_handler(conn: Connection):
    while True:
        msg = conn.recv()
        if msg == 'close':
            conn.close()
            print("Connection closed")
            break
        else:
            queue.put(msg)


def data_loop():
    processes = []
    connections = []

    address = ('hostname', 6060)     # family is deduced to be 'AF_INET'
    listener = Listener(address, authkey=b'secret password')
    print("Waiting for incoming connection...")

    while True:
        conn = listener.accept()  # dispatch listeners from here
        print('Connection accepted from', listener.last_accepted)
        p = Process(target=connection_handler, args=(conn,))
        p.start()
        processes.append(p)
        connections.append(conn)

    # [c.close() for c in connections]
    # [p.terminate() for p in processes]
    # listener.close()


def main():
    interval = 5
    app.layout = html.Div(
        [
            html.H1(children='Hello GPU'),
            html.Div(children='A dashboard for MTEC GPU utilization.'),

            dcc.Graph(id='live-graph', animate=True),
            dcc.Interval(
                id='graph-update',
                interval=interval*1000,
                n_intervals=0
            ),
        ]
    )

    main_process = Process(target=data_loop, args=())

    main_process.start()
    app.run_server(host='hostname', debug=False)
    main_process.terminate()


if __name__ == '__main__':
    main()
