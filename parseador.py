import json # Import standard json library for data serialization and deserialization
import jsonschema # Import jsonschema library to validate dictionary structures against our schema
import re # Import regular expression library for matching questions to grammar rules
import io # Import io library to check and handle in-memory file-like streams
from typing import Union, Dict, Any, List # Import type hints to enforce static typing signatures


#--------------------------------------------------------------------------------------------------------------------------
class GrammarParseError(Exception): # Define a custom exception for errors occurring during text-to-JSON parsing
    """Exception raised when plain text grammar rules cannot be parsed.""" # Docstring explaining the exception's purpose
    pass # Use pass because we only need to inherit from Exception without adding logic

class GrammarValidationError(Exception): # Define a custom exception for JSON schema validation failures
    """Exception raised when the grammar rules do not match the required JSON Schema.""" # Docstring explaining the exception's purpose
    pass # Use pass because we only need to inherit from Exception without adding logic

class QuestionValidationError(Exception): # Define a custom exception for questions that fail to match any grammar rule
    """Exception raised when a question does not match any provided grammar rule.""" # Docstring explaining the exception's purpose
    pass # Use pass because we only need to inherit from Exception without adding logic
#-----------------------------------------------------------------------------------------------------------------------------


RULES_SCHEMA = {
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "id": {
        "type": "string"
      },
      "pattern": {
        "type": "string",
        "description": "Regular expression pattern (should start with ^ and end with $)"
      },
      "intent": {
        "type": "string"
      }
    },
    "required": ["id", "pattern", "intent"]
  }
}

#WE'RE DECLARING THAT THIS FUNCTION COULD RECIVE A STRING OR A FILE-LIKE OBJECT
#THIS FUNCITION RECIVES AND READ THE INPUT
def _read_input_source(source: Union[str, io.IOBase]) -> str: # Define a helper function to extract text from a path or stream
    """Reads content from either a file path string or a file-like object.""" # Function docstring explaining behavior
    if isinstance(source, str): # Check if the provided source is a string (representing a file path)
        with open(source, 'r', encoding='utf-8') as f: # Open the file at the path in read mode with UTF-8 encoding
            return f.read() # Read and return the entire contents of the file
    else: # If the source is not a string, assume it is a file-like object
        return source.read() # Read and return the contents directly from the stream


# WE ARE RECIVING RULES,AND WE ARE VALIDATING IF THIS JSON IS SIMILAR TO OUR SCHEMA(RULES_SCHEMA) 
def _validate_and_compile_rules(rules_data: Dict[str, Any]) -> List[Dict[str, Any]]: # Define a helper function to validate schema and compile regex
    """Validates the rules dictionary against the JSON schema and compiles regex patterns.""" # Function docstring
    try: # Start a try block to catch jsonschema validation exceptions
        # WE NEED TO UNDERSTAND WHAT IS DOING jsonschema.validate()
        jsonschema.validate(instance=rules_data, schema=RULES_SCHEMA) # Validate the dictionary data against our predefined schema
        #IF SOMETHING GIVE AN ERROR WE ARE GOING TO SHOW THIS MESSAGE
    except jsonschema.exceptions.ValidationError as e: # Catch any validation errors raised by the library
        raise GrammarValidationError(f"Rules failed JSON Schema validation: {e.message}") from e # Raise our custom validation error with the specific message
    # WE ARE CREATING A COMPILED RULES
    compiled_rules = [] # Initialize an empty list to store rules with compiled regex objects
    for rule in rules_data: # Iterate through each rule defined in the validated data
        try: # Start a try block to catch invalid regex syntax exceptions
            compiled_pattern = re.compile(rule["pattern"]) # Attempt to compile the regex string into a regex object
        except re.error as e: # Catch regex compilation errors
            raise GrammarValidationError(f"Invalid regex pattern '{rule['pattern']}' in rule '{rule['id']}': {e}") from e # Raise custom error indicating bad regex
        compiled_rules.append({ # Append a new dictionary to the compiled rules list
            "id": rule["id"], # Copy the rule ID
            "compiled_pattern": compiled_pattern, # Store the compiled regex object
            "intent": rule["intent"] # Copy the intent string
        }) # Close append dictionary
    return compiled_rules # Return the list of compiled rules HERE WE ARE RETURNING A NEW DICTIONARY

def interpret_questions(rules_src: Union[str, io.IOBase], questions_src: Union[str, io.IOBase], output_dest: Union[str, io.IOBase] = "interpretation.txt") -> Union[str, bytes]: # Define the main public function
    """
    Parses grammar rules, validates questions against them, and produces a structured JSON interpretation.
    
    Args:
        rules_src: File path or file-like object containing grammar rules (JSON or text).
        questions_src: File path or file-like object containing questions (one per line).
        output_dest: File path or file-like object where the JSON output should be saved.
        
    Returns:
        The file path string if output_dest is a path, otherwise the JSON output as bytes.
    """ # Multi-line docstring detailing arguments and return values
    rules_content = _read_input_source(rules_src).strip() # Read and strip the raw content from the rules source
    
    try: # Start a try block for JSON decoding
            rules_data = json.loads(rules_content) # Parse the string as JSON into a dictionary
    except json.JSONDecodeError as e: # Catch JSON syntax errors
        raise GrammarParseError(f"Failed to parse rules as JSON: {e}") from e # Raise custom parsing error
    
    # if rules_content.startswith("{"): # Check if the content appears to be JSON by looking for an opening brace
        
    # else: # If it does not start with a brace, treat it as our custom plain text format
    #     rules_data = _parse_text_rules(rules_content) # Convert the plain text rules into a JSON-compatible dictionary
        
    compiled_rules = _validate_and_compile_rules(rules_data) # Validate the rules against the schema and compile all regex patterns
    
    questions_content = _read_input_source(questions_src) # Read the raw content from the questions source
    interpretations = [] # Initialize an empty list to store the interpretation results
    
    for line in questions_content.splitlines(): # Iterate over each question line
        question = line.strip() # Remove leading and trailing whitespace from the question
        if not question: # Check if the question line is empty
            continue # Skip processing for empty lines
            
        matched = False # Initialize a flag to track if the question matches any rule
        for rule in compiled_rules: # Iterate through the compiled rules checking for a match
            match = rule["compiled_pattern"].match(question) # Attempt to match the compiled regex against the current question
            if match: # If a match object is returned (meaning the pattern successfully matched)
                interpretations.append({ # Append a new structured dictionary to the interpretations list
                    "question": question, # Store the original question text
                    "rule_id": rule["id"], # Store the ID of the rule that matched
                    "intent": rule["intent"], # Store the intent associated with the matched rule
                    "extracted_groups": list(match.groups()) # Extract any regex capture groups and convert them to a list
                }) # Close append dictionary
                matched = True # Set the matched flag to True
                break # Break out of the inner loop since a rule was found
                
        if not matched: # Check if the flag is still False after checking all rules
            raise QuestionValidationError(f"Question '{question}' did not match any grammar rules.") # Raise custom validation error for unmatched question
            
    json_output_str = json.dumps(interpretations, indent=4) # Serialize the interpretations list into a formatted JSON string
    
    if isinstance(output_dest, str): # Check if the output destination is a file path string
        with open(output_dest, 'w', encoding='utf-8') as f: # Open the specified path in write mode with UTF-8 encoding
            f.write(json_output_str) # Write the JSON string to the file
        return output_dest # Return the string path as specified in the requirements
    else: # If the destination is a file-like object stream
        if isinstance(output_dest, io.TextIOBase): # Check if it is a text-based stream
            output_dest.write(json_output_str) # Write the string directly to the text stream
        else: # Otherwise, assume it is a binary stream
            output_dest.write(json_output_str.encode('utf-8')) # Encode the string to bytes and write to the binary stream
        return json_output_str.encode('utf-8') # Return the JSON data as a bytes object as requested
    


# # 1. Processing via File Paths
# # Reads rules.txt and questions.txt, writes JSON to output.json, and returns the path string.
# saved_path = interpret_questions("rules.json", "questions1.txt", "interpretacion.txt")
# print(f"Saved interpretation to: {saved_path}")