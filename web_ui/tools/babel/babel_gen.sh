#!/bin/bash

root_dir=../../application

pybabel extract -F $root_dir/babel.cfg -k _l -o messages.pot $root_dir/app

cp $root_dir/app/translations/en/LC_MESSAGES/messages.po $root_dir/app/translations/en/LC_MESSAGES/messages.po_bk
cp $root_dir/app/translations/ru/LC_MESSAGES/messages.po $root_dir/app/translations/ru/LC_MESSAGES/messages.po_bk

pybabel init -i messages.pot -d $root_dir/app/translations -l en
pybabel init -i messages.pot -d $root_dir/app/translations -l ru

rm messages.pot
