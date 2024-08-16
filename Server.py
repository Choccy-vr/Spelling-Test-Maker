from flask import Flask, render_template, request
from quickstart import FormGenerator
import webbrowser
class TestMakerServer:
    app = Flask(__name__)

    @app.route('/', methods=['GET', 'POST'])
    def home():
        if request.method == 'POST':
            _FormGenerator = FormGenerator(request.form.get(f'module'))
            for i in range(1, 26):
                word = request.form.get(f'word{i}')
                sentence = request.form.get(f'sentence{i}')
                _FormGenerator.set_variables(word, sentence, i)

            _FormGenerator.generate_form()

            # You can do further processing here (e.g., save to a database, generate a file, etc.)
            return "Form submitted successfully!"

        return render_template('index.html')


    if __name__ == '__main__':
        webbrowser.open('http://127.0.0.1:9000')
        app.run(host='127.0.0.1', port=9000)
        
