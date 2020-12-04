
## 问题

    需要更新的目录必须有 __init__.py !

## 完整的依赖项:

```code
pyquery
tornado
pymongo
motor

pyjade
```

## 使用 aytool:

```shell
pip3 install -i https://pypi.ayiis.me/simple/ --no-deps --upgrade aytool
```

```python
from aytool.spider import pyquery
```

## 更新服务器的包:

Just run:
```
bash build.bash
```

Just change the files and then:
```shell
    rm dist/* -f
    python3 setup.py sdist bdist_wheel
    python3 -m twine upload --repository-url https://pypi.ayiis.me/ dist/* && rm dist/* -f
    ayiis 123456
```

# Ref:

`python build pip server.md` In `paper`
