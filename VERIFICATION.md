# Перевірка блоку 6

Дата: 2026-10-25. Локальний Odoo 19, Python 3.12, PostgreSQL.
Базовий коміт блоку 5: `70cc8b1`. Новий репозиторій: `odoo-school-block6`,
гілка `19.0`, без remote та без push. Файли `sources/` не змінювались.

## Результати

| Перевірка | Результат |
|---|---|
| Встановлення `hr_hospital` з демо | Успішно, п'ять користувачів і зв'язки завантажені |
| Оновлення обох модулів, демо-база | **24 тести, 0 failed, 0 error(s)** |
| Чисте встановлення обох модулів без демо | **24 тести, 0 failed, 0 error(s)**; один демо-тест пропущено |
| Оновлення копії `odoo_block5_dev` | **20 тестів, 0 failed, 0 error(s)** |
| Незалежне встановлення email-модуля | **4 тести, 0 failed, 0 error(s)** |
| Видалення email-модуля | Індекс видаляється, контакти зберігаються |
| Перевірка pre-init на наявних дублікатах | Відмова з `UserError`, без автоматичного видалення контактів |
| Ruff | Усі перевірки пройдено |
| XML, manifest, RST, зображення | `scripts/check_static.py` пройдено |
| Docstrings | Є у всіх класів і методів models/wizard/report |
| PO | 163 перекладені записи, 0 порожніх/fuzzy; посилання Odoo збережені |
| Зміна мови | `Laziness` ↔ `Лінь`; `System User` ↔ `Користувач системи`; ієрархія хвороб українською |
| HTML у браузері | Обидва `index.html` відкриті; PNG-банери відображаються |
| Git diff | Перевірка пробілів пройдена |

Числа тестів взято з фінального `odoo.tests.result`, а не з `tests.stats`,
який також рахує службові setup/teardown. У фінальних прогонах модулів немає
WARNING/ERROR; немає попередження про одночасні at_install/post_install.
Очікувані повідомлення `Access Denied` виникають у негативних тестах.

## Тестове оточення

Створено окремі бази `odoo_block6_demo`, `odoo_block6_clean`,
`odoo_block6_upgrade`, `odoo_block6_email`. Upgrade-база — нейтралізована
копія блоку 5. Чинну базу та конфіг не змінено. Тестові журнали залишено
поза Git у `/tmp/block6-*.log` (тимчасові файли).

Ключові журнали: `/tmp/block6-final.log`, `/tmp/block6-clean.log`,
`/tmp/block6-upgrade.log`, `/tmp/block6-email-standalone.log`,
`/tmp/block6-email-lifecycle.log`. Під час першої спроби паралельного запуску
upgrade порт 8069 був зайнятий; повторний прогін на 8077 пройшов.

## Відтворення

Використовуйте Python з локального `odoo_dev/venv`, `odoo_dev/odoo/odoo-bin`
і `addons_path`, наведений у кореневому README. Приклади аргументів:

```text
-d odoo_block6_demo -u hr_hospital,partner_email_unique
--test-enable --test-tags=/hr_hospital,/partner_email_unique
--stop-after-init --no-http --http-port=8076 --http-interface=127.0.0.1
```

Статичні перевірки з кореня репозиторію:

```bash
/home/max-shelestiuk/odoo_dev/venv/bin/ruff check .
/home/max-shelestiuk/odoo_dev/venv/bin/python scripts/check_static.py
git diff --check
```

Для експорту використано `odoo.tools.translate.trans_export` у встановленому
Odoo; після заповнення `msgstr` каталог повторно експортовано скриптом
`scripts/export_uk.py`, що зберігає готові переклади за `msgid`. Повторний
експорт зараз не потрібен. Після нових змін джерел виконайте експорт знову.

## Основні змінені файли

- `hr_hospital/security/hospital_groups.xml`, `hospital_rules.xml`,
  `ir.model.access.csv`: ієрархія Odoo 19, ACL та домени доступу.
- `hr_hospital/demo/hospital_users_demo.xml`: п'ять зв'язаних користувачів.
- `hr_hospital/models/`, `views/`, `wizard/`, `report/`, `data/`:
  поле користувача пацієнта, англійські джерела, перекладні повідомлення,
  мовозалежна назва хвороби, docstrings та узгодження форм.
- `hr_hospital/i18n/uk_UA.po`, `migrations/19.0.6.0.0/post-migrate.py`:
  переклад і перенесення стандартних старих назв.
- `hr_hospital/tests/test_block6.py`, `test_block4.py`: права через with_user,
  методи блоку 3, мови та підтримка бази без демо.
- `hr_hospital/__manifest__.py`, `README.rst`, `changelog.rst`,
  `static/description/`: опис, іконка, банер.
- `partner_email_unique/`: окремий addon, індекс, pre-init hook, тести,
  документація, ліцензія та матеріали для Apps.
- `scripts/export_uk.py`, `scripts/check_static.py`: відтворювані перевірки.

## Ручні кроки

- Установити локальні паролі демо-користувачам і виконати приймальний вхід
  у UI під кожною роллю; серверні права вже перевірено через `with_user`.
- За потреби переключити власний запуск Odoo на новий addons_path та базу.
- Створити GitHub-репозиторії, налаштувати remote і виконати push лише після
  власного рішення про публікацію. Email-addon переноситься окремо без залежності
  від лікарняного модуля.
- Налаштувати акаунт Odoo Apps, доступ до приватного репозиторію, подати модуль
  і перевірити реальну сторінку маркету. Локальна готовність не є схваленням Apps.
- Надіслати ментору URL репозиторію, URL Apps і знімок опублікованої сторінки.

Не створювались акаунти, публікації, повідомлення ментору чи GitHub push.
