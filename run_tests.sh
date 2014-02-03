
#!/bin/bash
export DJANGO_SETTINGS_MODULE="stagecraft.settings.development"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

python manage.py test

# run style check
$basedir/pep-it.sh | tee "$outdir/pep8.out"
display_result $? 3 "Code style check"
