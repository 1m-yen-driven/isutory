# Isutory

ISUCONにおけるユーザーの挙動の確認ツール

## Requirements

- Graphviz
- python3

```
pip install -r requirements.txt
```

access.logは以下のラベルを含むLTSV形式であること

- uri
- method
- time

## How to use

`--user` で指定したラベル（ここではua=User Agent）単位で時系列順にアクセスを有向グラフ化

```
python3 isutory.py path/to/access.log --user ua
```

`--aggregates="^/api/isu.+","^/assets/.+"` のようにオプションで正規表現を使ってURIをまとめることができる

`--unified` を指定するとグラフを統合して、次にアクセスする可能性が高いノードへのエッジを濃く表示する
