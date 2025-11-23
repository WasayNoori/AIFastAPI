from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List

# Define schema
class Option(BaseModel):
    text: str
    isCorrect: bool
    imageUrl: str = ""

class Question(BaseModel):
    text: str
    category: str
    difficulty: int
    imageUrl: str = ""
    tags: str
    options: List[Option]

# Initialize parser and model
parser = PydanticOutputParser(pydantic_object=Question)
model = ChatOpenAI(model="gpt-4o", temperature=0.6)

# Prompt template
prompt = ChatPromptTemplate.from_template("""
You are a quiz question generator.
Generate 5–10 multiple-choice questions about the topic: "{topic}".

{format_instructions}
""")

# Combine
chain = prompt | model | parser

result = chain.invoke({"topic": "Photosynthesis", "format_instructions": parser.get_format_instructions()})
print(result.json(indent=2))
