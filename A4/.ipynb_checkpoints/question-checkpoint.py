import db
import json
from mcOption import MCOption
from rubric import Rubric
from bottle import response, request

class Question:
    def __init__(self, id, type, question_text, points, setup, answer):
        self.id = id
        self.type = type
        self.question_text = question_text
        self.points = points
        self.setup = setup
        self.answer = answer
    
    def update(self):
        with db.connect() as conn:
            cursor = conn.cursor();
            cursor.execute("UPDATE Questions SET type = ?, question_text = ?, points = ?, setup = ?, answer = ? WHERE id = ?",
                           (self.type, self.question_text, self.points, self.setup, self.answer, self.id))
            conn.commit();
            
    def updateFromJSON(self, question_data):
        if(self.type != question_data['type']):
            response.status = 400
            return "Cant change question type"
        self.type = question_data['type']
        self.question_text = question_data['question_text']
        self.points = question_data['points']
        self.setup = question_data['setup']
        self.answer = question_data['answer']
        self.update()
            
    def delete(self):
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Questions WHERE id = ?", (self.id, ))
            
    def jsonable(self):
        if(self.type == 'mc'):
            toAdd = {'id': self.id, 'type': self.type, 'question_text': self.question_text, 'points': self.points, 'setup': self.setup}
            with db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""SELECT *
                                  FROM MCOption
                                  WHERE MCOption.qid == %d"""%(toAdd['id']))
            true = []
            false = []
            result = cursor.fetchall();
            for mc in result:
                temp = MCOption(mc['id'], bool(mc['is_true']), mc['option_text'], mc['qid']).jsonable()
                if(mc['is_true'] == 1):
                    true.append(temp)
                else:
                    false.append(temp)
            toAdd['true_options'] = true
            toAdd['false_options'] = false
            return toAdd
        elif(self.type == 'sa'):
            toAdd = {'id': self.id, 'type': self.type, 'question_text': self.question_text, 'points': self.points, 'setup': self.setup, 'answer': self.answer}
            with db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""SELECT *
                                  FROM Rubric
                                  WHERE Rubric.qid == %d"""%(toAdd['id']))
            result = cursor.fetchall();
            rubrics = []
            for rubric in result:
                rubrics.append(Rubric(rubric['id'], rubric['rubric_text'], rubric['points'], rubric['qid']).jsonable())
            toAdd['rubrics'] = rubrics
            return toAdd
        else:
            return {'id': self.id, 'type': self.type, 'question_text': self.question_text, 'points': self.points, 'setup': self.setup, 'answer': self.answer}
    
        
    
    @staticmethod
    def setupBottleRoutes(app):
        @app.get('/question')
        def getQuestionIndex():
            with db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, type, question_text FROM Questions")
            result = cursor.fetchall();
            mc = []
            sql = []
            sa = []
            for q in result:
                temp = {
                    "id": q['id'],
                    "question_start": (q['question_text'])[:40]
                }
                if(q['type'] == 'mc'):
                    mc.append(temp)
                elif(q['type'] == 'sa'):
                    sa.append(temp)
                else:
                    sql.append(temp)
            response.status = 200
            return {
                "mc": mc,
                "sa": sa,
                "sql": sql
            }
        
        @app.get('/question/<id>')
        def getQuestionId(id):
            try:
                question = Question.find(id)
            except:
                response.status = 404
                return f"Question {id} not found"
            toAdd = question.jsonable()
            response.status = 200
            return toAdd
            
        @app.post('/question')
        def postQuestion():
            
            check = request.json
            if(check['question_text'] is None or check['question_text']== ''):
                response.status = 400
                return "Question Text is empty"
            if(check['type'] == 'sql' and check['setup'] is None):
                response.status = 400
                return "Setup is required for a sql question"
            if(check['points'] <= 0):
                response.status = 400
                return "points must be higher than 0"
            try:
                if(check['type'] != 'mc'):
                    check['answer']
            except Exception: 
                response.status = 400
                return "No answer provided"
            if(check['type'] != 'mc' and (check['answer'] is None or check['answer'] =='')):
                response.status = 400
                return "answer text must be provided if the question is SQL or SA"
            
            newQuestion = Question.createFromJSON(request.json)
            jsonQuestion = newQuestion.jsonable()
            if(jsonQuestion['type'] == 'sa' or jsonQuestion['type'] == 'sql'):
                with db.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""INSERT INTO Answers (answer_text, qid) VALUES (?, ?)""",(jsonQuestion['answer'], jsonQuestion['id']))
                    
            response.status = 200
            return jsonQuestion
        
        @app.put('/question/<id>')
        def putQuestion(id):
            try:
                question = Question.find(id)
            except Exception: 
                response.status = 404
                return f"Question {id} not found"
            response.status = 200
            question.updateFromJSON(request.json)
            return question.jsonable()
        
        @app.delete('/question/<id>')
        def deleteQuestion(id):
            try:
                question = Question.find(id)
            except:
                response.status = 404
                return f"Question {id} not found"
            qid = question.id
            if(question.type == 'mc'):
                with db.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""DELETE
                                      FROM MCOption
                                      WHERE MCOption.qid == %d"""%(qid))
                    result = cursor.fetchall()
            else:
                with db.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""DELETE
                                      FROM Answers
                                      WHERE Answers.qid == %d"""%(qid))
                    result = cursor.fetchall()
            if(question.type == 'sa'):
                with db.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""DELETE
                                      FROM Rubric
                                      WHERE Rubric.qid == %d"""%(qid))
                    result = cursor.fetchall()
            response.status = 200
            question.delete()
            response.content_type = 'application/json'
            return json.dumps(True)
    
    @staticmethod
    def createFromJSON(question_data):
        _answer = None
        _type = question_data['type']
        _question_text = question_data['question_text']
        _points = question_data['points']
        _setup = question_data['setup']
        if(_type != 'mc'):
            _answer = question_data['answer']
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Questions (type, question_text, points, setup, answer) VALUES (?, ?, ?, ?, ?)", 
                           (_type, _question_text, _points, _setup, _answer))
            conn.commit();
        return Question.find(cursor.lastrowid)
    
    @staticmethod
    def find(id):
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Questions WHERE id = ?", (id,))
            row = cursor.fetchone()

        if row is None:
            raise Exception(f'No such Question with id: {id}')
        else:
            return Question(row['id'], row['type'], row['question_text'], row['points'], row['setup'], row['answer'])