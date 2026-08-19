# みなと商店

Django で構築した EC サイトのデモアプリケーションです。商品閲覧からカート、クーポン適用、注文、確認メール送信までの一連のフローを実装しています。

> **Note:** Stripe 等の決済サービスは使用せず、カード情報の入力・保存のみで注文完了となります。本番 EC サイトを想定した決済・セキュリティ設計ではありません。

---

## デモ

| 項目 | 内容 |
| ---- | ---- |
| デモ URL（予定） | `https://hc-ec-site.herokuapp.com/products/` |
| 管理画面 | `/products/manage/products/`（Basic 認証: `admin` / `pw` ※デモ用） |

Heroku へのデプロイ後、上記 URL を更新予定です。

---

## 画面イメージ

| 商品一覧 | カート |
| -------- | ------ |
| ![商品一覧](./docs/screenshots/product_list.png) | ![カート](./docs/screenshots/cart.png) |

---

## 主な機能

**ユーザー向け**

- 商品一覧・詳細（関連商品の表示）
- カート（追加・数量変更・削除）
- プロモーションコードの適用
- 注文（請求先・カード情報入力）
- 注文完了メールの送信

**管理者向け**

- 商品の登録・編集・削除（Basic 認証）
- 注文一覧
- Django Admin
- 管理コマンド（初期商品投入、クーポンコード生成）

---

## 技術スタック

| カテゴリ | 技術 |
| -------- | ---- |
| 言語 / FW | Python 3.12 / Django 4.2 |
| DB | PostgreSQL |
| フロント | Bootstrap 5 |
| 画像 | Pillow（開発）/ Cloudinary（本番） |
| インフラ | Docker Compose（開発）/ Heroku, Gunicorn, WhiteNoise（本番） |

---

## 設計のポイント

- **カートの DB 永続化** — セッションに `cart_id` を保持し、カート内容は DB に保存
- **注文処理のトランザクション** — 注文作成・明細保存・クーポン使用済み更新・カートクリアを `transaction.atomic()` で一括処理
- **設定の環境分離** — `base` / `local` / `production` の 3 層構成

---

## ローカル環境構築

### 1. `.env` を作成

```env
DATABASE_URL="postgres://postgres:postgres@db:5432/django_develop"
SECRET_KEY=<Django SECRET_KEY>
EMAIL_HOST_USER=<Gmail アドレス（任意）>
EMAIL_HOST_PASSWORD=<Gmail アプリパスワード（任意）>
```

### 2. Docker を起動

```bash
docker-compose up --build
```

### 3. マイグレーション・初期データ

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py seed_products
docker-compose exec web python manage.py promotion_code_generate
```

### 4. アクセス

- 商品一覧: http://localhost:3000/products/
- 管理画面: 商品一覧右上の「商品管理画面を見る」から遷移（Basic 認証: `admin` / `pw` ※デモ用）

> **管理画面への導線について**  
> 商品一覧に管理画面へのボタンを置いています。実際の EC サイトでは、一般ユーザー向けのページから管理画面へリンクすることはありませんが、本プロジェクトではポートフォリオとして管理機能を確認しやすくするため、このボタンを設置しています。

---

## ディレクトリ構成

```
config/          … プロジェクト設定
product/         … EC 機能（models, views, forms, templates）
fixtures/        … seed 用の商品画像（元データ）
docs/            … README 用スクリーンショット
media/           … 実行時に Django が保存する商品画像
docker-compose.yml
Dockerfile
Procfile         … Heroku 用
requirements.txt
```
