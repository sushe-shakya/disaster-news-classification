from settings import get_required_values, shared_components
from bson.json_util import dumps, loads
from flask import request, Response
import json
import ast
import logging

logger = logging.getLogger(__file__)


def create_news():
    """
       Function to create new newss.
    """
    db = shared_components["db"]
    collection = db.news
    try:
        # Create new newss
        if request.json:
            body = request.json
        else:
            raise TypeError("Invalid Request Format")

        record_id = collection.insert(body)
        return Response("Successfully created the resource", status=201)

    except Exception as e:
        # Error while trying to create the resource
        print("Exception: {}".format(e))
        return Response("Error while trying to create resource")


def fetch_all_news():
    """
       Function to fetch all the news.
       """
    db = shared_components["db"]
    collection = db.news
    try:
        # Fetch all the record(s)
        records_fetched = collection.find()

        # Check if the records are found
        if records_fetched.count() > 0:
            # Prepare the response
            records = dumps(records_fetched)
            resp = Response(records, status=200, mimetype='application/json')
            return resp
        else:
            # No records are found
            return Response("No records are found", status=404)
    except Exception as e:
        print("Exception: {}".format(e))
        # Error while trying to fetch the resource
        return Response("Error while trying to fetch the resource", status=500)


def fetch_news_by_type():
    """
       Function to fetch the news by type.
       """
    db = shared_components["db"]
    collection = db.news
    try:
        if request.json:
            body = request.json
            logger.info(f"Request:{body}")
        else:
            raise TypeError("Invalid Request Format")

        disaster_type = body["disasterType"]

        records_fetched = []

        _ = collection.find({"disasterType": disaster_type})
        # Check if the records are found
        if _.count() > 0:
            # Prepare the response
            records_fetched += loads(dumps(_))

        # Check if the records are found
        if records_fetched:

            required_keys = ["news", "disasterType", "link", "date"]
            records_fetched = get_required_values(
                records_fetched, required_keys)

            # Prepare the response
            resp = Response(dumps(records_fetched), status=200,
                            mimetype='application/json')
            return resp

        else:
            # No records are found
            return Response("No records are found", status=404)
    except Exception as e:
        print("Exception: {}".format(e))
        # Error while trying to fetch the resource
        return Response("Error while trying to fetch the resource", status=500)


def update_news(news_id):
    """
       Function to update the news.
       """

    db = shared_components["db"]
    collection = db.news
    try:
        # Get the value which needs to be updated
        if request.json:
            body = ast.literal_eval(json.dumps(request.json))
        else:
            raise TypeError("Invalid request format")

        # Updating the news
        records_updated = collection.update_one(
            {"id": int(news_id)}, {"$set": body})

        # Check if resource is updated
        if records_updated.modified_count > 0:
            # Prepare the response as resource is updated successfully
            return Response("Resource updated successfully", status=200)
        else:
            # Bad request as the resource is not available to update
            # Add message for debugging purpose
            return Response("Resource not available", status=404)
    except Exception as e:
        # Error while trying to update the resource
        # Add message for debugging purpose
        print("Exception: {}".format(e))
        return Response("Error while updating the resource", status=500)


def remove_news(news_id):
    """
       Function to remove the news.
       """
    db = shared_components["db"]
    collection = db.news
    try:
        # Delete the news
        delete_news = collection.delete_one({"id": int(news_id)})

        if delete_news.deleted_count > 0:
            # Prepare the response
            return Response("Resource deleted successfully", status=200)
        else:
            # Resource Not found
            return Response("Resource Not Found", status=404)
    except Exception as e:
        # Error while trying to delete the resource
        # Add message for debugging purpose
        print("Exception: {}".format(e))
        return Response("Resource deletion failed", status=500)
