# Odoo School — практичний блок 6

Репозиторій створений із завершеного блоку 5 зі збереженням Git-історії.
Робоча гілка — `19.0`. Зовнішні репозиторії та публікації не створювались.

- [hr_hospital/README.rst](hr_hospital/README.rst): ролі, доступ, демо-користувачі,
  українська локалізація, встановлення та тести.
- [partner_email_unique/README.rst](partner_email_unique/README.rst): незалежний
  модуль унікальних email контактів та підготовка до Odoo Apps.
- [VERIFICATION.md](VERIFICATION.md): результати перевірок і ручні кроки.

Обидва модулі лежать на один рівень нижче кореня репозиторію. Додавайте саме
корінь до `addons_path`, уникаючи другої копії `hr_hospital` з попередніх блоків.

Локальний запуск підготовленої демо-бази (окремий порт):

```bash
/home/max-shelestiuk/odoo_dev/venv/bin/python \
  /home/max-shelestiuk/odoo_dev/odoo/odoo-bin \
  --addons-path=/home/max-shelestiuk/odoo_dev/odoo/addons,/home/max-shelestiuk/odoo_dev/custom_addons/odoo-school-block6 \
  -d odoo_block6_demo --http-port=8076 --http-interface=127.0.0.1
```

Паролі демо-користувачів задаються локально адміністратором. Чинний конфіг
Odoo та базу блоку 5 не змінено.
