from functools import total_ordering
import os
import re
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# a helper method for pagination


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, PUT, POST, DELETE, OPTIONS')
        return response
    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/api/v1/categories')
    def retrieve_categories():
        # `GET '/api/v1/categories'`

        # - Fetches a dictionary of categories in which the keys are the ids and the value is the corresponding string of the category
        # - Request Arguments: None
        # - Returns: An object with a single key, `categories`, that contains an object of `id: category_string` key: value pairs.
        '''json
        {
            "categories": {
                "1": "Science",
                "2": "Art",
                "3": "Geography",
                "4": "History",
                "5": "Entertainment",
                "6": "Sports"
            },
            "success": true
        }
        '''

        categories = Category.query.all()
        categories_dict = {}

        # condition to check if there are categories
        if categories is None:
            return not_found(404)

        for category in categories:
            categories_dict[category.id] = category.type
        return jsonify({
            'success': True,
            'categories': categories_dict
        })
    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route('/api/v1/questions', methods=['GET'])
    def retrieve_questions():

        # `GET '/api/v1/questions'`

        # - Fetches a list of dictionaries of questions, answers, category_ids and a dictionary of categories in which the keys are the ids and the value is the corresponding string of the category
        # - Request Arguments: None
        # - Returns: An object with three keys, `categories`, `current_category` and  `questions`, that contains an object of `id: category_string` key: value pairs, `current_category` and `questions list of categories``.
        '''json
        {
            "categories": {
                "1": "Science",
                "2": "Art",
                "3": "Geography",
                "4": "History",
                "5": "Entertainment",
                "6": "Sports"
            },
            "current_category": null,
            "questions": [
                {
                    "answer": "Edward Scissorhands",
                    "category": 5,
                    "difficulty": 3,
                    "id": 6,
                    "question": "What was the title of the 1990 fantasy directed by Tim Burton about a young man with multi-bladed appendages?"
                }
                ],
                "success": true
                "total_questions": 17
        }
        '''

        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        categories = Category.query.all()
        categories_dict = {}

        # condition to check if the server has any questions
        if len(current_questions) == 0:
            return not_found(404)

        # condition to check if the server is running
        if selection is None:
            return server_error(500)

        # condition to check if the server has any categories
        if categories is None:
            return not_found(404)
        for category in categories:
            categories_dict[category.id] = category.type
        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'categories': categories_dict,
            'current_category': None,
        })

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route('/api/v1/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):

        # `DELETE '/api/v1/questions/<int:question_id>'`

        # - Delete the question from the database
        # - Request Arguments: None
        # - Returns: An object with with a key of deleted and a value of the deleted question_id, and a key of message with the successfull deletion and updates the list of questions otherwise it will error 404 if the question_id is not found
        '''json
        {
            "deleted": 20,
            "message": "Question deleted successfully.",
            "questions": [
                {
                    "answer": "Edward Scissorhands",
                    "category": 5,
                    "difficulty": 3,
                    "id": 6,
                    "question": "What was the title of the 1990 fantasy directed by Tim Burton about a young man with multi-bladed appendages?"
                }
                ],
                "status_code": 200,
                "success": true,
                "total_questions": 15
        }
        '''

        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            if question is None:
                return not_found(404)
            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'status_code': 200,
                'deleted': question_id,
                'message': 'Question deleted successfully.',
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })
        except:
            return unprocessable(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/api/v1/questions', methods=['POST'])
    def create_question():

        # `POST '/api/v1/questions'`

        # - Creates a new question and save it to the database
        # - Request Arguments: none
        # - Returns: An object with a single key, `categories`, that contains an object of `id: category_string` key: value pairs.
        '''json
        {
            "categories": {
                "1": "Science",
                "2": "Art",
                "3": "Geography",
                "4": "History",
                "5": "Entertainment",
                "6": "Sports"
            },
            "success": true
        }
        '''

        body = request.get_json()
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)

        if new_question is None or new_answer is None or new_difficulty is None or new_category is None:
            return unprocessable(422)
        try:
            question = Question(question=new_question, answer=new_answer,
                                difficulty=new_difficulty, category=new_category)
            question.insert()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'message': 'Question created successfully.',
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })
        except:
            return unprocessable(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/api/v1/questions/search', methods=['POST'])
    def search_questions():

        # `GET '/api/v1/questions/search'`

        # - Queries the database searching for a question based on the search term.
        # - Request Arguments: None
        # - Returns: Returns a list of questions that matches the search term.

        body = request.get_json()
        search_term = body.get('searchTerm', None)

        # current_questions = paginate_questions(request, selection)
        categories = Category.query.all()
        categories_dict = {}

        if categories is None:
            return not_found(404)

        if search_term == '':
            return bad_request(400)

        for category in categories:
            categories_dict[category.id] = category.type

        if search_term:
            search_result = Question.query.filter(
                Question.question.ilike(f'%{search_term}%')).all()

            return jsonify({
                'success': True,
                'questions': [question.format() for question in search_result],
                'total_questions': len(Question.query.all()),
                'categories': categories_dict,
                'current_category': None
            })

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/api/v1/categories/<int:category_id>/questions')
    def retrieve_questions_by_category(category_id):

        # `POST '/api/v1/categories/<int:category_id>/questions'`

        # - Gets questions based on category_id
        # - Request Arguments: none
        # - Returns: A list of questions in the specified category.
        '''json
        {
            "categories": {
                "1": "Science",
                "2": "Art",
                "3": "Geography",
                "4": "History",
                "5": "Entertainment",
                "6": "Sports"
            },
            "current_category": 5,
            "questions": [
                {
                    "answer": "Edward Scissorhands",
                    "category": 5,
                    "difficulty": 3,
                    "id": 6,
                    "question": "What was the title of the 1990 fantasy directed by Tim Burton about a young man with multi-bladed appendages?"
                }
            ],
            "success": true,
            "total_questions": 12
        }
        '''

        selection = Question.query.filter(
            Question.category == category_id).all()
        current_questions = paginate_questions(request, selection)
        categories = Category.query.all()
        categories_dict = {}

        # if category_id is greater than length of categories return 404 errorhandler
        if category_id > len(categories):
            return not_found(404)

        if categories is None:
            return not_found(404)
        for category in categories:
            categories_dict[category.id] = category.type
        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'categories': categories_dict,
            'current_category': category_id
        })

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/api/v1/quizzes', methods=['POST'])
    def play_quiz():

        # `GET '/api/v1/questions'`

        # - Fetches one question at a time from selected category or all questions
        # - Request Arguments: None
        # - Returns:One question at a time is displayed, the user is allowed to answer

        body = request.get_json()

        if not ('quiz_category' in body and 'previous_questions' in body):
            return unprocessable(422)

        previous_questions = body.get('previous_questions')
        quiz_category = body.get('quiz_category')

        try:
            if quiz_category['id'] == 0:
                selection = Question.query.filter(
                    Question.id.notin_(previous_questions)).all()
            else:
                selection = Question.query.filter(
                    Question.category == quiz_category['id'],
                    Question.id.notin_(previous_questions)).all()
            if len(selection) == 0:
                return jsonify({
                    'success': True,
                    'question': None
                })
            else:
                random_question = selection[random.randrange(
                    0, len(selection))].format()
                return jsonify({
                    'success': True,
                    'question': random_question
                })
        except:
            return server_error(500)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    @app.errorhandler(405)
    def forbidden(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "internal server error"
        }), 500

    return app
