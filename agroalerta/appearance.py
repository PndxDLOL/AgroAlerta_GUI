"""Apariencia por sesión. No cambia configuración global ni los datos."""
LIGHT=dict(bg="#f4f7f5",panel="#ffffff",sidebar="#e7efeb",text="#173d34",muted="#5e746a",line="#d7e2dc",accent="#197253",grid="#e7eeea")
DARK=dict(bg="#0c1415",panel="#152222",sidebar="#101d1e",text="#e7f4ed",muted="#a6bbb2",line="#2d4541",accent="#7ce0af",grid="#29423e")

def palette(mode):return DARK if mode=="oscuro" else LIGHT

def css(mode):
    p=palette(mode)
    return f"""<style>
    :root {{color-scheme:{'dark' if mode=='oscuro' else 'light'};}}
    .stApp,[data-testid=stAppViewContainer],header[data-testid=stHeader] {{background:{p['bg']};color:{p['text']};}}
    [data-testid=stSidebar] {{background:{p['sidebar']};}}
    .block-container {{padding-top:4rem;padding-bottom:2rem;max-width:1560px;}}
    h1,h2,h3,h4,[data-testid=stMetricValue],[data-testid=stMetricLabel],label,p,li {{color:{p['text']};}}
    .eyebrow {{font-size:.73rem;letter-spacing:.16em;color:{p['muted']};font-weight:700;}}
    .intro {{font-size:1.02rem;color:{p['muted']};margin-bottom:.7rem;}}
    .pill {{display:inline-block;background:{p['sidebar']};border:1px solid {p['line']};color:{p['accent']};padding:5px 12px;border-radius:20px;font-size:.8rem;margin:0 6px 8px 0;}}
    [data-testid=stMetric] {{background:{p['panel']};border:1px solid {p['line']};border-radius:12px;padding:14px;min-height:112px;}}
    [data-testid=stMetricValue] {{font-size:1.5rem!important;}}
    [data-testid=stMetricLabel] {{min-height:2.6rem;height:auto!important;}}
    [data-testid=stMetricLabel] p,[data-testid=stMetricLabel] div {{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;}}
    [data-testid=stCaptionContainer] p {{color:{p['muted']};}}
    [data-testid=stHorizontalBlock] {{gap:1rem;}}
    [data-baseweb=select] > div,[data-baseweb=input],input,textarea,[data-baseweb=popover],ul[role=listbox] {{background:{p['panel']}!important;color:{p['text']}!important;}}
    [data-baseweb=select] span,[data-baseweb=select] input,[role=option],button p {{color:{p['text']}!important;}}
    button[kind=secondary],button[kind=tertiary],[data-testid=stFileUploaderDropzone] {{background:{p['panel']};color:{p['text']};border-color:{p['line']};}}
    button[kind=primary] p {{color:white!important;}}
    [data-testid=stExpander] details,[data-testid=stJson],[data-testid=stCode] {{background:{p['panel']};border-color:{p['line']};}}
    [data-testid=stMarkdownContainer] code {{background:{p['sidebar']};color:{p['accent']};}}
    .stAlert p {{color:{p['text']};}}
    [role=tab] {{color:{p['text']};}}
    </style>"""

def theme_figure(fig,mode):
    p=palette(mode)
    fig.update_layout(template="plotly_dark" if mode=="oscuro" else "plotly_white",
        paper_bgcolor=p["bg"],plot_bgcolor=p["panel"],font_color=p["text"],title_font_color=p["text"],
        colorway=["#4f9fef","#aa86df","#33b1ae","#de79ae","#8ca655"])
    fig.update_xaxes(gridcolor=p["grid"],linecolor=p["line"],title_font_color=p["text"],tickfont_color=p["muted"])
    fig.update_yaxes(gridcolor=p["grid"],zerolinecolor=p["line"],title_font_color=p["text"],tickfont_color=p["muted"])
    if mode=="oscuro":
        for trace in fig.data:
            if getattr(trace,"line",None) and isinstance(trace.line.color,str) and trace.line.color=="#1c6650":trace.line.color="#78dcb2"
            if getattr(trace,"marker",None) and isinstance(trace.marker.color,str) and trace.marker.color=="#1c6650":trace.marker.color="#78dcb2"
    return fig
