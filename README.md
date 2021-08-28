# Isutory

ISUCONにおけるユーザーの挙動の確認ツール

## Requirements

- Graphviz
- python3

```
pip install -r requirements.txt
```

## How to use

`--identifier` で指定したラベル（ここではua=User Agent）単位で時系列順にアクセスを有向グラフ化

```
python3 isutory.py path/to/access.log --identifier ua
```

`--aggregates="^/api/isu.+","^/assets/.+"` のようにオプションで正規表現を使ってURIをまとめることができる

`--ignore="^/js/.+","^/css/.+"` のようにオプションで無視するURIを指定できる

`--unified` を指定するとグラフを統合して、次にアクセスする可能性が高いノードへのエッジを濃く表示する

`--statistics` を指定すると、グラフを作成する代わりに統計情報を得られる

## example

```
python3 isutory.py access.log --a="/api/condition/[^/]+$","/api/isu/[^/]+$","/api/isu/[^/]+/icon$","/api/isu/[^/]+/icon$","/assets/.+$","/api/isu/.+graph.*$","/isu/[^/]+/condition$","/[^/]*$","/isu/[^/]+$","/isu/[^/]+/graph$" --s
```
