workon codeminer
sudo systemctl start rabbitmq
celery -A codeminer worker -l info
python manage.py runserver
