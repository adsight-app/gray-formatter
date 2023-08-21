from remove_trailing_comma._main import _fix_src

with open("test.py", "r") as f:
    content = f.read()
    print(_fix_src(content))