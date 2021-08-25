# Isutory

ISUCONにおけるユーザーの挙動の確認ツール

## Requirements

python3

```
pip install -r requirements.txt
```

access.logは以下のラベルを含むLTSV形式であること

- uri
- method
- time

## How to use

--userで指定したラベル（ここではua=User Agent）単位で時系列順にアクセスを有向グラフ化

```
python3 isutory.py path/to/access.log --user ua
```

`--aggregates="^/api/isu.+","^/assets/.+"` のようにオプションで正規表現を使ってURIをまとめることができる
