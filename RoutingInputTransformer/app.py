import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import base64
from io import BytesIO
import pandas as pd

app = dash.Dash(__name__)

# Declare server for Heroku deployment. Needed for Procfile.
server = app.server

# Define custom styles
app.layout = html.Div(style={'backgroundColor': '#f5f5f5', 'padding': '20px'}, children=[
    html.Div(className='card', children=[
        html.H1("Routing Input Transformer", style={'textAlign': 'center', 'color': '#333333'}),
        html.H2("Upload File", style={'textAlign': 'center', 'color': '#333333'}),
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            multiple=False
        ),
        html.Button('Submit', id='submit-button', n_clicks=0, style={'margin': '10px'}),
        dcc.Loading(
            id="loading",
            type="default",
            children=html.Div(id='loading-output'),
        ),
    ]),
    html.Div(id='file-info', style={'marginTop': '20px'}),
    html.Div(id='output-table-container', style={'overflowX': 'auto', 'marginTop': '20px'}),
    html.Div(className='card', children=[
        html.H2("Download Transformed File", style={'textAlign': 'center', 'color': '#333333'}),
        html.A("Download", id="download-link", download="data.xlsx", href="", style={'margin': '10px'})
    ])
])


def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'xls' in filename:
            df = pd.read_excel(BytesIO(decoded))
        elif 'csv' in filename:
            df = pd.read_csv(BytesIO(decoded))
        else:
            return html.Div('Unsupported file type')
    except Exception as e:
        return html.Div([
            'There was an error processing this file.'
        ])
    return df


# Define a function to create the Excel file on the server
def save_excel(df):
    path = 'data.xlsx'
    df.to_excel(path, index=False)
    return path


@app.callback(Output('loading-output', 'children'),
              Output('output-table-container', 'children'),
              Output('download-link', 'href'),
              Output('file-info', 'children'),
              Input('submit-button', 'n_clicks'),
              State('upload-data', 'contents'),
              State('upload-data', 'filename'))
def update_output(n_clicks, contents, filename):
    if n_clicks > 0 and contents is not None:
        processed_data = parse_contents(contents, filename)

        if isinstance(processed_data, pd.DataFrame):
            processed_data['groupid'] = processed_data['groupid_pickup'] + processed_data['groupid_delivery'] + processed_data['tags']

            path = save_excel(processed_data)

            file_info = f"File name: {filename}, Columns: {len(processed_data.columns)}, Rows: {len(processed_data)}"
            return None, dash_table.DataTable(
                id='table',
                columns=[{'name': col, 'id': col} for col in processed_data.columns],
                data=processed_data.to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
            ), f"/download/{path}", file_info
        else:
            return html.Div(processed_data)

    return None, None, "", None


if __name__ == '__main__':
    app.run_server(debug=True)

