from flask import Flask
from backend.routes import register_routes
from database.db import create_table

# Initialize Flask and configure custom frontend folders.
app = Flask(
    __name__,
    template_folder='frontend/templates',
    static_folder='frontend/static',
    instance_relative_config=True,
)
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE='database/debugdiary.db',
)

register_routes(app)

# Ensure the database table exists before the first request.
with app.app_context():
    create_table()


if __name__ == '__main__':
    app.run(debug=True)
