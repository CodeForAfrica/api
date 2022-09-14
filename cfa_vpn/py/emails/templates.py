import urllib


def get_outline_email_template(key):
    return f"""
                    <div>
                        <p>
                        Follow the instructions on your <a href="https://s3.amazonaws.com/outline-vpn/invite.html#{urllib.parse.quote(key.access_url)}">Invitation Link</a> to download the Outline app and get connected.
                        </p>
                        <p>Having trouble accessing the invitation link?</p>
                        <ol>
                            <li>Copy your access key: {key.access_url}</li>
                            <li>Follow our invitation instructions on GitHub: https://github.com/Jigsaw-Code/outline-client/blob/master/docs/invitation_instructions.md</li>
                        </ol>
                    </div>
                """
