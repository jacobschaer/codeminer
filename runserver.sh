workon codeminer
sudo systemctl start rabbitmq
celery -A codeminer worker -l info
python manage.py runserver
export NEO4J_BOLT_URL=bolt://neo4j:password@localhost