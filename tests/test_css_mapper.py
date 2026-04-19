from dsl.converter.css_mapper import map_css_to_style


def test_basic_color():
    assert map_css_to_style({"background-color": "#ff0000"}) == {"bgColor": "#ff0000"}


def test_font_size():
    assert map_css_to_style({"font-size": "24px"}) == {"fontSize": 24}


def test_font_weight_bold():
    assert map_css_to_style({"font-weight": "bold"}) == {"bold": True}


def test_font_weight_normal():
    assert map_css_to_style({"font-weight": "normal"}) == {"bold": False}


def test_border_radius():
    assert map_css_to_style({"border-radius": "8px"}) == {"cornerRadius": 8}


def test_opacity():
    assert map_css_to_style({"opacity": "0.5"}) == {"opacity": 0.5}


def test_padding():
    assert map_css_to_style({"padding": "20px"}) == {"padding": 20}


def test_unknown_property_ignored():
    assert map_css_to_style({"cursor": "pointer"}) == {}


def test_width_height():
    assert map_css_to_style({"width": "100px", "height": "50px"}) == {"width": 100, "height": 50}


def test_flex_layout():
    assert map_css_to_style({"display": "flex", "flex-direction": "column"}) == {"layout": "vertical"}
