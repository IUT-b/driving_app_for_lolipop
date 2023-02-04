from flask import Blueprint, jsonify, request

from ..api import calculation

api = Blueprint("api", __name__)


@api.get("/")
def index():
    return jsonify({"column": "value"}), 201


@api.post("/classification")
def classification():
    return calculation.classification(request)
