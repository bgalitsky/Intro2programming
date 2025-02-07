import os
from configparser import RawConfigParser

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from facebook_autopost import FacebookAutoPost

complaint_reply = """
    I’m sorry to hear about the trouble you experienced with your reservation. Here are links where you can report your complaint, seek assistance, and potentially request compensation from Airbnb:

    1. **Airbnb Help Center**: You can visit the [Airbnb Help Center](https://www.airbnb.com/help) to find information on how to report problems and get assistance related to your reservation.

    2. **Contact Airbnb Support**: For direct support, you can reach out through the Airbnb app or website. Here’s the link to contact support directly: [Contact Airbnb Support](https://www.airbnb.com/contact).

    3. **Report a Listing**: To report the listing as fraudulent, you can use this link: [Report a Listing](https://www.airbnb.com/report).

    4. **File a Complaint or Request Refund**: If you are seeking compensation, you can file a complaint through this link: [Request a Refund](https://www.airbnb.com/help/article/1395/how-do-i-request-a-refund).

    For additional reporting, you can also consider the social media presence of the business. You may report your complaint on their Facebook page as well. Here’s the link: <#https://www.facebook.com/airbnb/#>. 

    I hope this helps, and you get your issue resolved quickly!
    """
class FacebookAutoPostBot:
    def __init__(self, config_path='config.ini'):
        # Load configuration
        config = RawConfigParser()
        config.read(config_path)

        # Facebook credentials
        self.email = config.get('Facebook', 'email')
        self.password = config.get('Facebook', 'password')

        # API keys
        self.gemini_api_key = config.get('Gemini', 'api_key')
        os.environ["OPENAI_API_KEY"] = config.get('OpenAI', 'api_key')

        # Automation settings
        self.post_interval = config.getint('Automation', 'post_interval')
        self.profile_name = config.get('Automation', 'profile_name')

        # Initialize the chatbot model
        self.model = ChatOpenAI(model="gpt-4o-mini")

        # Define the prompt template
        self.prompt = ChatPromptTemplate.from_template(
            "For given complaint, please find links to complain, report my problem and seek assistance/compensation '{"
            "complaint}'. In the end of the response, provide Facebook link of the business to report complain wrapped in  "
            "'<#' and '#>'."
        )

        # Define the chain
        self.chain = (
            {"complaint": RunnablePassthrough()}
            | self.prompt
            | self.model
            | StrOutputParser()
        )

        self.bot =  FacebookAutoPost(
            email=self.email,
            password=self.password,
            gemini_api_key=self.gemini_api_key,
            post_prompt="",
            post_interval=self.post_interval,
            profile_name=self.profile_name
        )

    def generate_complaint_links(self, user_complaint):
        """Generates complaint links using the AI chain."""
        #links_with_comments = self.chain.invoke("complaint:" + user_complaint)
        links_with_comments = 'https://www.facebook.com/airbnb'
        return links_with_comments

    def extract_facebook_url(self, response_text):
        """Extracts the Facebook link from the response."""
        return self.find_between(response_text, '<#', '#>')

    @staticmethod
    def find_between(text, start, end):
        """Helper function to extract a substring between two markers."""
        start_idx = text.find(start) + len(start)
        end_idx = text.find(end, start_idx)
        return text[start_idx:end_idx] if start_idx > len(start) - 1 and end_idx != -1 else None

    def post_complaint(self, user_complaint):
        response = self.generate_complaint_links(user_complaint)
        #url = self.extract_facebook_url(response)
        url = 'https://www.facebook.com/airbnb'
        #self.bot.make_a_comment_on_facebook(user_complaint, url)
        #return response
        return complaint_reply


    '''
    I made a reservation long in advance and contacted the owner a day in advance but no response. Then I found reviews 
    for this owner citing that the listing is fake. Arbnb should have removed it, otherwise they do a systematic fraud
    '''