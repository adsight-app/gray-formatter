from gray_formatter._main import main

def get_content():
    with open("test.py", "r") as f:
        content = f.read()
    return content

content = get_content()
try:
    main(("test.py",))
    print(get_content())
except Exception as e:
    raise e
finally:
    with open("test.py", "w") as f:
        f.write(content)