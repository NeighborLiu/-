ENV_JSON_GENERATION_PROMPT = """
You are a helpful assistant that generates tool specifications for a toolkit in JSON format.
The tool specifications MUST include the following information:
- name: the name of the tool
- description: a brief description of the tool
- parameters: a list of parameters that the tool accepts:
  - type: its type must be one of [integer, number, boolean, object, array]
  - properties: the detailed information about the parameters
    - paramter_name: The name of the parameter when calling this tool. For a single parameter, it contains the following two arguments:
      - type: the data type of the parameter, it must be one of [integer, number, boolean, object, array]
      - description: a brief description of the parameter
  - required: a list of required parameters which must be inputted when invoking the tool.
- returns: a list of returns of the tool, each return should contain `name`, `type`, and `description`.
- exceptions: a list of exceptions of the tool, each exception should contain `name` and `description`.

For example, if the toolkit is Email toolkit and one of its tool is to send an email, the tool specifications should look like this:
""
{
  "name": "send_email",
  "description": "Send an email to someone.",
  "parameters": {
    "type": "object",
    "properties": {
      "sender": {
        "type": "string",
        "description": "The email's sender."
      },
      "receiver": {
        "type": "array",
        "description": "The email's receiver(s).",
        "items": {
          "type": "string",
          "description": "the receiver's email address"
        }
      },
      "title": {
        "type": "string",
        "description": "The email's title."
      },
      "content": {
        "type": "string",
        "description": "The email's content."
      },
      "attachment": {
        "type": "string",
        "description": "The local path of the attachment file."
      }
    },
    "required": [
      "receiver",
      "content"
    ]
  },
  "returns": [
    {
      "name": "result",
      "type": "object",
      "description": "An object containing 'success' (boolean, indicates whether the email was sent successfully), 'email_id' (string, the unique identifier of the email, if successful), and 'error_message' (string, if unsuccessful)."
    }
  ],
  "exceptions": [
    {
      "name": "InvalidRequestException",
      "description": "The email address in the 'sender' and 'receiver' parameter is empty or do not fit the email address format (e.g., example@gmail.com)"
    }
  ]
}
""

You should follow the template to generate a new tool description for $toolkit_name, and the description of this toolkit is as follows: $toolkit_description. The generated tool should satisfy the description of the toolkit, and should not contain same tool name we already have in our toolkit: $already_tool_name. Your answer MUST output in JSON format.
"""