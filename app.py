from flask import Flask, request, send_file, render_template
from mido import MidiFile, MidiTrack, Message
from collections import defaultdict
import random
import io

app = Flask(__name__)

# 예제 노트 시퀀스 (학습 데이터를 제공할 수 있음)
example_notes = [60, 62, 64, 65, 67, 69, 71, 72]


# 상태 전환 확률 테이블 생성 함수
def create_transition_table(notes):
    transition_table = defaultdict(lambda: defaultdict(int))
    for i in range(len(notes) - 1):
        current_note = notes[i]
        next_note = notes[i + 1]
        transition_table[current_note][next_note] += 1

    for current_note, transitions in transition_table.items():
        total = sum(transitions.values())
        for next_note in transitions:
            transitions[next_note] /= total

    return transition_table


# 마코프 체인을 이용한 음악 생성 함수
def generate_music(transition_table, start_note, length=50):
    music = [start_note]
    current_note = start_note

    for _ in range(length - 1):
        if current_note in transition_table:
            next_notes = list(transition_table[current_note].keys())
            probabilities = list(transition_table[current_note].values())
            current_note = random.choices(next_notes, probabilities)[0]
            music.append(current_note)
        else:
            break

    return music


# MIDI 파일로 저장하는 함수
def save_to_midi(notes):
    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)

    for note in notes:
        track.append(Message("note_on", note=note, velocity=64, time=0))
        track.append(Message("note_off", note=note, velocity=64, time=480))

    # 메모리 스트림에 저장하여 반환
    midi_data = io.BytesIO()
    midi.save(file=midi_data)
    midi_data.seek(0)
    return midi_data


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    start_note = data.get("start_note", 60)
    length = data.get("length", 50)
    transition_table = create_transition_table(example_notes)
    generated_music = generate_music(
        transition_table, start_note=start_note, length=length
    )
    midi_data = save_to_midi(generated_music)

    return send_file(
        midi_data,
        as_attachment=True,
        download_name="generated_music.mid",
        mimetype="audio/midi",
    )


if __name__ == "__main__":
    app.run(debug=True, port=8000)
