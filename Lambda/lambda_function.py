from __future__ import print_function
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import datetime
import json


# These are my AWS IoT login and certificates
host = "*********.iot.us-east-1.amazonaws.com"
cert_path = "cert/"
rootCAPath = cert_path + "root-CA.crt"
certificatePath = cert_path + "*********-certificate.pem.crt"
privateKeyPath = cert_path + "*********-private.pem.key"
shadowName = "CoffeeMachine"



def lambda_handler(event, context):
    global myAWSIoTMQTTShadowClient, myDeviceShadow
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print ('RECEIVED EVENT: ' + json.dumps(event, separators=(',', ':')))
    if 'session' in event:
        print("event.session.application.applicationId=" + event['session']['application']['applicationId'])

        """
        Uncomment this if statement and populate with your skill's application ID to
        prevent someone else from configuring a skill that sends requests to this
        function.
        """
        if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.*********"):
            raise ValueError("Invalid Application ID")

        if event['session']['new'] and 'requestId' in event['request']:
            on_session_started({'requestId': event['request']['requestId']},event['session'])

        if 'request' in event:
            # Init AWSIoTMQTTClient
            myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(shadowName+"_Lambda_"+event['request']['requestId'][-12:])
            myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
            myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

            # AWSIoTMQTTClient connection configuration
            myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
            myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
            myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

            # Connect to AWS IoT Shadow
            myAWSIoTMQTTShadowClient.connect()
            myDeviceShadow = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(shadowName, True)
            
            if event['request']['type'] == "LaunchRequest":
                return on_launch(event['request'], event['session'])
            elif event['request']['type'] == "IntentRequest":
                return on_intent(event['request'], event['session'])
            elif event['request']['type'] == "SessionEndedRequest":
                return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId'] + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they want """

    print("on_launch requestId=" + launch_request['requestId'] + ", sessionId=" + session['sessionId'])

    # Dispatch to your skill's launch
    intent = launch_request
    return Welcome_response(intent, session)


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] + ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "WelcomeIntent":
        return Welcome_response(intent, session)
    elif intent_name == "CoffeeChoiceIntent":
        return CoffeeChoice_response(intent, session)
    elif intent_name == "RegularStrengthIntent":
        return RegularStrength_response(intent, session)
    elif intent_name == "NumberOfCupsIntent":
        return NumberOfCups_response(intent, session)

    elif intent_name == "ReadyIntent":
        return Ready_response(intent, session)
    elif intent_name == "NotReadyIntent":
        return NotReady_response(intent, session)

    elif intent_name == "StopIntent":
        return Stop_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return Stop_response()

    elif intent_name == "HelpIntent":
        return Help_response()
    elif intent_name == "AMAZON.HelpIntent":
        return Help_response()

    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] + ", sessionId=" + session['sessionId'])

    # add cleanup logic here
    return Stop_response()





# Shadow callback for updating the AWS IoT
def IoTShadowCallback_Update(payload, responseStatus, token):
    print("IoT update response: " + responseStatus.upper())



# --------------- Functions that control the skill's behavior ------------------


def Welcome_response(intent, session):
    # Set Session Attributes
    CoffeeChoice = ''
    RegularStrength = ''
    NumberOfCups = ''

    # Set other defaults
    card_title = "Welcome"
    should_end_session = False

    # Start the real task
    currentTime = datetime.datetime.now()
    if currentTime.hour < 12:
        printTime = "morning"
    elif 12 <= currentTime.hour < 18:
        printTime = "afternoon"
    else:
        printTime = "evening"
    
    speech_output = "Good " + printTime + ", your Coffee Machine will switch on. " \
                    "What kind of coffee do you want? " \
                    "I have Regular, Cappucino, Macchiato and Latte"
    reprompt_text = "What kind of coffee do you want? " \
                    "I have Regular, Cappucino, Macchiato and Latte"

    if 'slots' in intent:
        if 'CoffeeChoice' in intent['slots']:
            if 'value' in intent['slots']['CoffeeChoice']:
                CoffeeChoice = intent['slots']['CoffeeChoice']['value'].upper()

                if (CoffeeChoice == "REGULAR COFFEE" or CoffeeChoice == "REGULAR"):
                    CoffeeChoice = 'REGULAR'
                    RegularStrength = 'MEDIUM'

                    speech_output = "Good " + printTime + ", your Coffee Machine will switch on. " \
                                    "Excellent choice, I like " + CoffeeChoice + " coffee. " \
                                    "Make your choice between Dark, Medium or Mild"
                    reprompt_text = "Make your choice between Dark, Medium or Mild"

                elif (CoffeeChoice == "CAPPUCCINO" or CoffeeChoice == "MACCHIATO" or CoffeeChoice == "LATTE"):
                    NumberOfCups = 'ONE'

                    speech_output = "Good " + printTime + ", your Coffee Machine will switch on. " \
                                    "Excellent choice, I like " + CoffeeChoice + ". " \
                                    "Did you put in water, milk and one coffee pad?"
                    reprompt_text = "Did you put in water, milk and one coffee pad?"


    # Publish to AWS IoT Shadow
    myJSONPayload = "{ \"state\" : {"\
                                    "\"desired\": {"\
                                                    "\"Power\": \"ON\", "\
                                                    "\"Start\": \"NO\", "\
                                                    "\"CoffeeChoice\": \"" + CoffeeChoice + "\", "\
                                                    "\"RegularStrength\": \"" + RegularStrength + "\", "\
                                                    "\"NumberOfCups\": \"" + NumberOfCups + "\""\
                                                "} "\
                                    ", \"reported\": {"\
                                                    "\"Start\": \"NO\" "\
                                                "} "\
                                    "} "\
                    "}"
    myDeviceShadow.shadowUpdate(myJSONPayload, IoTShadowCallback_Update, 5)
    print ('UPLOADED TO IoT: ' + json.dumps(json.loads(myJSONPayload), separators=(',', ':')))
    
    # Send response back to the Alexa Voice Skill
    session_attributes = create_attributes(CoffeeChoice,RegularStrength,NumberOfCups)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def CoffeeChoice_response(intent, session):
    # Set Session Attributes
    if 'attributes' in session:
        if 'CoffeeChoice' in session['attributes']:
            CoffeeChoice = session['attributes']['CoffeeChoice']
        else:
            CoffeeChoice = ''
        if 'RegularStrength' in session['attributes']:
            RegularStrength = session['attributes']['RegularStrength']
        else:
            RegularStrength = ''
        if 'NumberOfCups' in session['attributes']:
            NumberOfCups = session['attributes']['NumberOfCups']
        else: 
            NumberOfCups = ''
    else:
        CoffeeChoice = ''
        RegularStrength = ''
        NumberOfCups = ''

    # Set other defaults
    card_title = "CoffeeChoice"
    should_end_session = False

    speech_output = "I didn't understand. What kind of coffee do you want? " \
                    "I have Regular, Cappucino, Macchiato and Latte"
    reprompt_text = "I have Regular, Cappucino, Macchiato and Latte"

    # Start the real task
    if 'slots' in intent:
        if 'CoffeeChoice' in intent['slots']:
            if 'value' in intent['slots']['CoffeeChoice']:
                CoffeeChoice = intent['slots']['CoffeeChoice']['value'].upper()

                if (CoffeeChoice == "REGULAR COFFEE" or CoffeeChoice == "REGULAR"):
                    CoffeeChoice = 'REGULAR'
                    RegularStrength = 'MEDIUM'

                    speech_output = "Excellent choice, I like " + CoffeeChoice + " coffee. " \
                                    "Make your choice between Dark, Medium or Mild"
                    reprompt_text = "Make your choice between Dark, Medium or Mild"

                elif (CoffeeChoice == "CAPPUCCINO" or CoffeeChoice == "MACCHIATO" or CoffeeChoice == "LATTE"):
                    NumberOfCups = 'ONE'

                    speech_output = "Excellent choice, I like " + CoffeeChoice + ". " \
                                    "Did you put in water, milk and one coffee pad?"
                    reprompt_text = "Did you put in water, milk and one coffee pad?"

        
    # Publish to AWS IoT Shadow
    myJSONPayload = "{ \"state\" : {"\
                                    "\"desired\": {"\
                                                    "\"Power\": \"ON\", "\
                                                    "\"Start\": \"NO\", "\
                                                    "\"CoffeeChoice\": \"" + CoffeeChoice + "\", "\
                                                    "\"RegularStrength\": \"" + RegularStrength + "\", "\
                                                    "\"NumberOfCups\": \"" + NumberOfCups + "\""\
                                                "} "\
                                    ", \"reported\": {"\
                                                    "\"Start\": \"NO\" "\
                                                "} "\
                                    "} "\
                    "}"
    myDeviceShadow.shadowUpdate(myJSONPayload, IoTShadowCallback_Update, 5)
    print ('UPLOADED TO IoT: ' + json.dumps(json.loads(myJSONPayload), separators=(',', ':')))

    # Send response back to the Alexa Voice Skill
    session_attributes = create_attributes(CoffeeChoice,RegularStrength,NumberOfCups)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))



def RegularStrength_response(intent, session):
    # Set Session Attributes
    if 'attributes' in session:
        if 'CoffeeChoice' in session['attributes']:
            CoffeeChoice = session['attributes']['CoffeeChoice']
        else:
            CoffeeChoice = ''
        if 'RegularStrength' in session['attributes']:
            RegularStrength = session['attributes']['RegularStrength']
        else:
            RegularStrength = ''
        if 'NumberOfCups' in session['attributes']:
            NumberOfCups = session['attributes']['NumberOfCups']
        else: 
            NumberOfCups = ''
    else:
        CoffeeChoice = ''
        RegularStrength = ''
        NumberOfCups = ''

    # Set other defaults
    card_title = "RegularStrength"
    should_end_session = False
    speech_output = "Make your choice between Dark, Medium or Mild"
    reprompt_text = "Make your choice between Dark, Medium or Mild"

    # Start the real task
    if 'slots' in intent:
        if 'RegularStrength' in intent['slots']:
            if 'value' in intent['slots']['RegularStrength']:
                RegularStrength = intent['slots']['RegularStrength']['value'].upper()

                # If user did give other but similar phrases
                if RegularStrength == "STRONG":
                    RegularStrength = "DARK"
                if RegularStrength == "NORMAL":
                    RegularStrength = "MEDIUM"

                speech_output = RegularStrength + " it will be. Do you want one or two cups?"
                reprompt_text = "Do you want one or two cups?"

                CoffeeChoice = 'REGULAR'
                
    # Publish to AWS IoT Shadow
    myJSONPayload = "{ \"state\" : {"\
                                    "\"desired\": {"\
                                                    "\"Power\": \"ON\", "\
                                                    "\"Start\": \"NO\", "\
                                                    "\"CoffeeChoice\": \"" + CoffeeChoice + "\", "\
                                                    "\"RegularStrength\": \"" + RegularStrength + "\", "\
                                                    "\"NumberOfCups\": \"" + NumberOfCups + "\""\
                                                "} "\
                                    ", \"reported\": {"\
                                                    "\"Start\": \"NO\" "\
                                                "} "\
                                    "} "\
                    "}"
    myDeviceShadow.shadowUpdate(myJSONPayload, IoTShadowCallback_Update, 5)
    print ('UPLOADED TO IoT: ' + json.dumps(json.loads(myJSONPayload), separators=(',', ':')))

    # Send response back to the Alexa Voice Skill
    session_attributes = create_attributes(CoffeeChoice,RegularStrength,NumberOfCups)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def NumberOfCups_response(intent, session):
    # Set Session Attributes
    if 'attributes' in session:
        if 'CoffeeChoice' in session['attributes']:
            CoffeeChoice = session['attributes']['CoffeeChoice']
        else:
            CoffeeChoice = ''
        if 'RegularStrength' in session['attributes']:
            RegularStrength = session['attributes']['RegularStrength']
        else:
            RegularStrength = ''
        if 'NumberOfCups' in session['attributes']:
            NumberOfCups = session['attributes']['NumberOfCups']
        else: 
            NumberOfCups = ''
    else:
        CoffeeChoice = ''
        RegularStrength = ''
        NumberOfCups = ''

    # Set other defaults
    card_title = "NumberOfCups"
    should_end_session = False
    speech_output = "Do you want one or two cups?"
    reprompt_text = "Do you want one or two cups?"

    # Start the real task
    if 'slots' in intent:
        if 'NumberOfCups' in intent['slots']:
            if 'value' in intent['slots']['NumberOfCups']:
                NumberOfCups = intent['slots']['NumberOfCups']['value'].upper()

                # If user did give other but similar phrasses
                if NumberOfCups == "BIG" or NumberOfCups == "LARGE" or NumberOfCups == "2" or NumberOfCups == "DOUBLE":
                    NumberOfCups = "TWO"
                if NumberOfCups == "SMALL" or NumberOfCups == "1" or NumberOfCups == "SINGLE":
                    NumberOfCups = "ONE"
                    
                if (NumberOfCups == "ONE"):
                    speech_output = "Did you put in water and one coffee pad?"
                    reprompt_text = "Did you put in water and one coffee pad?"
                else:
                    speech_output = "Did you put in water and two coffee pads?"
                    reprompt_text = "Did you put in water and two coffee pads?"
    
    # Publish to AWS IoT Shadow
    myJSONPayload = "{ \"state\" : {"\
                                    "\"desired\": {"\
                                                    "\"Power\": \"ON\", "\
                                                    "\"Start\": \"NO\", "\
                                                    "\"CoffeeChoice\": \"" + CoffeeChoice + "\", "\
                                                    "\"RegularStrength\": \"" + RegularStrength + "\", "\
                                                    "\"NumberOfCups\": \"" + NumberOfCups + "\""\
                                                "} "\
                                    ", \"reported\": {"\
                                                    "\"Start\": \"NO\" "\
                                                "} "\
                                    "} "\
                    "}"
    myDeviceShadow.shadowUpdate(myJSONPayload, IoTShadowCallback_Update, 5)
    print ('UPLOADED TO IoT: ' + json.dumps(json.loads(myJSONPayload), separators=(',', ':')))

    # Send response back to the Alexa Voice Skill
    session_attributes = create_attributes(CoffeeChoice,RegularStrength,NumberOfCups)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def Ready_response(intent, session):
    # Set Session Attributes
    if 'attributes' in session:
        if 'CoffeeChoice' in session['attributes']:
            CoffeeChoice = session['attributes']['CoffeeChoice']
        else:
            CoffeeChoice = ''
        if 'RegularStrength' in session['attributes']:
            RegularStrength = session['attributes']['RegularStrength']
        else:
            RegularStrength = ''
        if 'NumberOfCups' in session['attributes']:
            NumberOfCups = session['attributes']['NumberOfCups']
        else: 
            NumberOfCups = ''
    else:
        CoffeeChoice = ''
        RegularStrength = ''
        NumberOfCups = ''

    # Set other defaults
    card_title = "StartBrewing"
    should_end_session = True

    # Start the real task
    if (((CoffeeChoice <> "" and CoffeeChoice <> "REGULAR") or (CoffeeChoice == "REGULAR" and RegularStrength <> "")) and NumberOfCups <> ""):
        if NumberOfCups == 'TWO':
            CupCups = 'cups'
        else:
            CupCups = 'cup'

        speech_output = "Thank you, I'll now prepare you " + NumberOfCups + " nice " + CupCups + " of " + RegularStrength + " " + CoffeeChoice
        reprompt_text = ""

        # Publish to AWS IoT Shadow
        myJSONPayload = "{ \"state\" : {"\
                                    "\"desired\": {"\
                                                    "\"Power\": \"ON\", "\
                                                    "\"Start\": \"YES\", "\
                                                    "\"CoffeeChoice\": \"" + CoffeeChoice + "\", "\
                                                    "\"RegularStrength\": \"" + RegularStrength + "\", "\
                                                    "\"NumberOfCups\": \"" + NumberOfCups + "\""\
                                                "} "\
                                    "} "\
                    "}"
        myDeviceShadow.shadowUpdate(myJSONPayload, IoTShadowCallback_Update, 5)
        print ('UPLOADED TO IoT: ' + json.dumps(json.loads(myJSONPayload), separators=(',', ':')))

    else:
        speech_output = "Something went wrong, please start over by asking for Help"
        reprompt_text = "Something went wrong, please start over by asking for Help"

    # Send response back to the Alexa Voice Skill
    session_attributes = create_attributes(CoffeeChoice,RegularStrength,NumberOfCups)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def NotReady_response(intent, session):
    # Set Session Attributes
    if 'attributes' in session:
        if 'CoffeeChoice' in session['attributes']:
            CoffeeChoice = session['attributes']['CoffeeChoice']
        else:
            CoffeeChoice = ''
        if 'RegularStrength' in session['attributes']:
            RegularStrength = session['attributes']['RegularStrength']
        else:
            RegularStrength = ''
        if 'NumberOfCups' in session['attributes']:
            NumberOfCups = session['attributes']['NumberOfCups']
        else: 
            NumberOfCups = ''
    else:
        CoffeeChoice = ''
        RegularStrength = ''
        NumberOfCups = ''

    # Set other defaults
    card_title = "NotReady"
    should_end_session = False

    # Start the real task
    speech_output = "Ok, I will wait a little moment, tell me when you are ready."
    reprompt_text = "Hurry up, tell me when you are ready"

    # Send response back to the Alexa Voice Skill
    session_attributes = create_attributes(CoffeeChoice,RegularStrength,NumberOfCups)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def Help_response():
    # Set Session Attributes
    CoffeeChoice = ''
    RegularStrength = ''
    NumberOfCups = ''

    # Set other defaults
    card_title = "Help"
    should_end_session = False

    # Start the real task
    speech_output = "Let me help you, what kind of coffee do you want? " \
                    "I have Regular, Cappucino, Macchiato and Latte"
    reprompt_text = "What kind of coffee do you want? " \
                    "I have Regular, Cappucino, Macchiato and Latte"
        
    # Send response back to the Alexa Voice Skill
    session_attributes = create_attributes(CoffeeChoice,RegularStrength,NumberOfCups)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def Stop_response():
    session_attributes = {}
    card_title = "Stop"

    # Setting this to true ends the session and exits the skill.
    should_end_session = True

    CoffeeChoice = ''
    RegularStrength = ''
    NumberOfCups = ''

    speech_output = "Your coffee machine will power off. Have a nice day!"
    reprompt_text = None

    # Connect and publish to AWS IoT Shadow
    myJSONPayload = "{ \"state\" : {"\
                                "\"desired\": {"\
                                                "\"Power\": \"OFF\", "\
                                                "\"Start\": \"NO\", "\
                                                "\"CoffeeChoice\": \"\", "\
                                                "\"RegularStrength\": \"\", "\
                                                "\"NumberOfCups\": \"\" "\
                                            "} "\
                                "} "\
                "}"
    myDeviceShadow.shadowUpdate(myJSONPayload, IoTShadowCallback_Update, 5)
    print ('UPLOADED TO IoT: ' + json.dumps(json.loads(myJSONPayload), separators=(',', ':')))

    session_attributes = create_attributes(CoffeeChoice,RegularStrength,NumberOfCups)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))




# --------------- Helpers that build all of the responses ----------------------

def create_attributes(CoffeeChoice, RegularStrength, NumberOfCups):
    return {"CoffeeChoice": CoffeeChoice.upper(), "RegularStrength": RegularStrength.upper(), "NumberOfCups": NumberOfCups.upper()}


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
