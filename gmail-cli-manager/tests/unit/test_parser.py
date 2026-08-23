"""Unit tests for email parser."""

from email.message import EmailMessage

from gmail_manager.email.parser import EmailParser


def test_parse_simple_message() -> None:
    """Test parsing a simple text message."""
    msg = EmailMessage()
    msg["Subject"] = "Test Subject"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg.set_payload("Hello, World!")

    content = EmailParser.parse(msg)

    assert content.subject == "Test Subject"
    assert content.from_address == "sender@example.com"
    assert "recipient@example.com" in content.to_addresses
    assert content.text_body == "Hello, World!"
    assert not content.is_multipart


def test_parse_html_message() -> None:
    """Test parsing an HTML message."""
    msg = EmailMessage()
    msg["Subject"] = "HTML Test"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg.set_content("<html><body>Hello!</body></html>", subtype="html")

    content = EmailParser.parse(msg)

    assert content.subject == "HTML Test"
    assert "<html>" in content.html_body


def test_parse_with_attachments() -> None:
    """Test parsing a message with attachments."""
    msg = EmailMessage()
    msg["Subject"] = "With Attachment"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg.set_content("Body text")
    msg.add_attachment(b"file content", maintype="application", subtype="pdf", filename="test.pdf")

    content = EmailParser.parse(msg)

    assert content.is_multipart
    assert len(content.attachments) == 1
    assert content.attachments[0]["filename"] == "test.pdf"


def test_has_attachments() -> None:
    """Test attachment detection."""
    msg_no_att = EmailMessage()
    msg_no_att.set_content("No attachments")
    assert not EmailParser.has_attachments(msg_no_att)

    msg_with_att = EmailMessage()
    msg_with_att.set_content("Has attachment")
    msg_with_att.add_attachment(b"data", maintype="application", subtype="pdf", filename="file.pdf")
    assert EmailParser.has_attachments(msg_with_att)


def test_get_attachment_names() -> None:
    """Test getting attachment filenames."""
    msg = EmailMessage()
    msg.set_content("Message")
    msg.add_attachment(b"data1", maintype="application", subtype="pdf", filename="doc.pdf")
    msg.add_attachment(b"data2", maintype="image", subtype="png", filename="image.png")

    names = EmailParser.get_attachment_names(msg)

    assert "doc.pdf" in names
    assert "image.png" in names
    assert len(names) == 2
