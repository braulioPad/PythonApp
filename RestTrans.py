from flask import Flask, request, jsonify
from langdetect import detect
from googletrans import Translator
from pydub import AudioSegment
from pydub.playback import play
import speech_recognition as sr
import os
from pydub.silence import split_on_silence
from flask_cors import CORS  # Import CORS


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def detect_language(text):
    try:
        language = detect(text)
        return language
    except Exception as e:
        # Handle exceptions, e.g., if the text is too short
        print(f"Error: {e}")
        return None
    
def translate_paragraph(paragraph, target_language):
    translator = Translator()
    translation = translator.translate(paragraph, dest=target_language)
    return translation.text

@app.route('/detect-and-translate', methods=['POST'])
def detect_and_translate():
    if not request.json or 'paragraph' not in request.json or 'target_language' not in request.json:
        return jsonify({'error': 'Paragraph and target_language are required in the JSON payload'}), 400

    paragraph = request.json['paragraph']
    target_language = request.json['target_language']
    print("text: "+paragraph);
    # Detect the language of the input paragraph
    source_language = detect_language(paragraph)

    if source_language:
        # Translate the paragraph to the target language
        translated_paragraph = translate_paragraph(paragraph, target_language)

        return jsonify({
            'source_language': source_language,
            'target_language': target_language,
            'original_paragraph': paragraph,
            'translated_paragraph': translated_paragraph
        })
    else:
        return jsonify({'error': 'Language detection failed'}), 500

@app.route('/detect-language', methods=['POST'])
def detect_language_endpoint():
    if not request.json or 'paragraph' not in request.json:
        return jsonify({'error': 'Paragraph is required in the JSON payload'}), 400

    paragraph = request.json['paragraph']
    language = detect_language(paragraph)

    if language:
        return jsonify({'detected_language': language})
    else:
        return jsonify({'error': 'Language detection failed'}), 500

""" ----------------- """   

def translate_text(text, target_language):
    translator = Translator()
    translation = translator.translate(text, dest=target_language)
    return translation.text

# Create a speech recognition object
r = sr.Recognizer()

# A function to recognize speech in the audio file
def transcribe_audio(path):
    with sr.AudioFile(path) as source:
        audio_listened = r.record(source)
        # Try converting it to text
        text = r.recognize_google(audio_listened)
    return text

# A function that splits the audio file into chunks on silence
# and applies speech recognition
def get_large_audio_transcription_on_silence(path):
    sound = AudioSegment.from_file(path)
    chunks = split_on_silence(sound, min_silence_len=500, silence_thresh=sound.dBFS-14, keep_silence=500)
    folder_name = "audio-chunks"
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    whole_text = ""
    for i, audio_chunk in enumerate(chunks, start=1):
        chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
        audio_chunk.export(chunk_filename, format="wav")
        try:
            text = transcribe_audio(chunk_filename)
        except sr.UnknownValueError as e:
            print("Error:", str(e))
        else:
            text = f"{text.capitalize()}. "
            print(chunk_filename, ":", text)
            whole_text += text
    return whole_text

@app.route('/transcribe-audio', methods=['POST'])
def transcribe_audio_endpoint():
    if 'audio' not in request.files:
        return jsonify({'error': 'Audio file is required in the request'}), 400

    audio_file = request.files['audio']
    target_language = request.form['target_language']

    # Save the uploaded audio file
    audio_path = "uploaded_audio.wav"
    audio_file.save(audio_path)

    try:
        recognized_text = get_large_audio_transcription_on_silence(audio_path)
        if recognized_text:
            # Translate the recognized text to the target language
            translated_text = translate_text(recognized_text, target_language)
            print(f"Translated text: {translated_text}")

            return jsonify({
                'recognized_text': recognized_text,
                'target_language': target_language,
                'translated_text': translated_text
            })
        else:
            return jsonify({'error': 'Audio recognition failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up the uploaded audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)


if __name__ == '__main__':
    app.run(debug=True)