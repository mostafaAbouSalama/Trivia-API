import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

#   A function to paginate questions into pages of 10 questions
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

  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app)

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

  '''
  @TODO:
  Create an endpoint to handle GET requests
  for all available categories.
  '''
  @app.route('/categories')
  def retrieve_categories():
      query_of_categories = Category.query.all()
      categories_dict = {}
      #   Format the category dictionary as the frontend needs
      for category in query_of_categories:
          categories_dict[category.id] = category.type
      #   making sure we got categories from database
      if len(categories_dict) == 0:
          abort(404)
      return jsonify({
        'success': True,
        'categories': categories_dict
      })

  '''
  @TODO:
  Create an endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''
  @app.route('/questions')
  def retrieve_questions():
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)
      query_of_categories = Category.query.all()
      categories_dict = {}
      for category in query_of_categories:
          categories_dict[category.id] = category.type
      #   Making sure we got questions from database and after passing the pagination
      if len(current_questions) == 0:
          abort(404)
      return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(selection),
        'categories': categories_dict
      })

  '''
  @TODO:
  Create an endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''
  @app.route('/questions/<int:id>', methods=['DELETE'])
  def delete_question(id):
      try:
          #   Grabing that one question by its id
          question = Question.query.filter(Question.id == id).one_or_none()
          if question is None:
              abort(404)
          question.delete()
          #   Re-Query to reload questions after one of them has been deleted
          selection = Question.query.order_by(Question.id).all()
          current_questions = paginate_questions(request, selection)
          return jsonify({
            'success': True,
            'deleted': id,
            'questions': current_questions,
            'total_questions': len(selection)
          })
      except:
          abort(422)

  '''
  @TODO:
  Create an endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''

  '''
  @TODO:
  Create a POST endpoint to get questions based on a search term.
  It should return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.
  '''
  @app.route('/questions', methods=['POST'])
  def create_or_search_for_question():
      body = request.get_json()
      #   Capturing the values of the forms to check later if this is a search or adding a new question
      new_question = body.get('question', None)
      new_answer = body.get('answer', None)
      new_category = body.get('category', None)
      new_difficulty = body.get('difficulty', None)
      search = body.get('searchTerm')
      try:
          #   If search is truthy then we search its value
          if search:
              selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search)))
              current_questions = paginate_questions(request, selection)
              return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(selection.all())
              })
          else:
              #   If search is falsy, then we try to add a new questions
              #   Making sure all form values are written and not blank.
              if ((new_question is None) or (new_answer is None) or (new_category is None) or (new_difficulty is None)):
                  abort(422)
              question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
              question.insert()
              selection = Question.query.order_by(Question.id).all()
              current_questions = paginate_questions(request, selection)
              return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
              })
      except:
          abort(422)
  '''
  @TODO:
  Create a GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''
  @app.route('/categories/<int:id>/questions')
  def retrieve_category_questions(id):
      selection = Question.query.filter(Question.category == id).all()
      current_questions = paginate_questions(request, selection)
      query_of_categories = Category.query.all()
      categories_dict = {}
      for category in query_of_categories:
          categories_dict[category.id] = category.type
      if len(current_questions) == 0:
          abort(404)
      return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(selection),
        'current_category': id,
        'categories': categories_dict
      })

  '''
  @TODO:
  Create a POST endpoint to get questions to play the quiz.
  This endpoint should take category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''
  @app.route('/quizzes', methods=['POST'])
  def play_quiz():
      body = request.get_json()
      #   Grab the quiz category and list of previously asked questions if we are in the middle of the quiz
      category = body.get('quiz_category', None)
      previous_questions = body.get('previous_questions')
      #   If both or one of them is None then we have a bad request and abort
      if (category is None) or (previous_questions is None):
          abort(400)
      category_id = int(category['id'])
      #   Make sure we have a unique set of previously asked questions where no question is repeated
      prev_questions_uniq = set(previous_questions)
      #   Check for the category id to query the respective category questions or all questions
      if category_id == 0:
          questions = Question.query.all()
      else:
          questions = Question.query.filter(Question.category == category_id).all()
      #   List comprehension conditional (always wanted to try this :D).
      #   looping over the newly respective queried questions just above.
      #   Then checking if any of them was not asked before in the quiz.
      #   If so, I add it to a new list quiz_questions which I will use to feed
      #   the quiz itself
      quiz_questions = [question for question in questions if question.id not in prev_questions_uniq]
      if len(quiz_questions) > 0:
          #   Check we have questions in our newly made quiz_questions list
          #   If so, I pick one question from it randomly
          the_question = quiz_questions[random.randint(0, len(quiz_questions) - 1)]
          return jsonify({
            'success': True,
            'question': the_question.format()
          })
      else:
          return jsonify({
            'success': True
          })


  '''
  @TODO:
  Create error handlers for all expected errors
  including 404 and 422.
  '''

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False,
      "error": 400,
      "message": "bad request"
      }), 400

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

  @app.errorhandler(500)
  def server_error(error):
    return jsonify({
      "success": False,
      "error": 500,
      "message": "internal server error"
      }), 500

  return app
