import json
import random

from app.models.entities import Test
from app.models.enums import Role, TestStatus


def can_view_test(test: Test, user) -> bool:
    if test.status == TestStatus.PUBLISHED:
        return True
    if test.author_id == user.id:
        return True
    if user.role == Role.TEACHER:
        return test.subject_id in {subject.id for subject in user.teaching_subjects}
    return False


def serialize_test_list_item(test: Test, attempted: bool = False):
    return {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "difficulty": test.difficulty,
        "status": test.status,
        "subject_name": test.subject.name,
        "author_name": test.author.full_name,
        "moderation_comment": test.moderation_comment,
        "question_count": len(test.questions),
        "attempted": attempted,
    }


def serialize_test_detail(test: Test):
    return {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "difficulty": test.difficulty,
        "status": test.status,
        "subject_name": test.subject.name,
        "author_name": test.author.full_name,
        "moderation_comment": test.moderation_comment,
        "questions": [
            serialize_question(question)
            for question in sorted(test.questions, key=lambda item: item.sort_order)
        ],
    }


def serialize_question(question):
    payload = json.loads(question.payload) if question.payload else {}
    matching_pairs = payload.get("pairs", [])
    matching_options = [pair["right"] for pair in matching_pairs]
    return {
        "id": question.id,
        "text": question.text,
        "points": question.points,
        "question_type": question.question_type,
        "sort_order": question.sort_order,
        "options": [
            {
                "id": option.id,
                "text": option.text,
                "sort_order": option.sort_order,
                "is_correct": option.is_correct,
            }
            for option in sorted(
                question.answer_options, key=lambda item: item.sort_order
            )
        ],
        "matching_left": [pair["left"] for pair in matching_pairs],
        "matching_options": random.sample(matching_options, len(matching_options))
        if matching_options
        else [],
        "correct_answer": payload.get("correct_answer"),
        "matching_pairs": [
            {"left": p["left"], "right": p["right"]} for p in matching_pairs
        ],
    }
