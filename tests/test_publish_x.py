"""Tests for publish_x: parsing, X length, image mapping, checks and posting (X client mocked)."""
import base64
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, create_autospec, patch

import pytest
import requests
import tweepy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from publish_x import check, main, make_client, parse, publish, x_length  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "hcompany-catalog-recall-agent" / "x.md"
HCOMPANY_IMAGES = ("use-cases.png", "hcompany-execution.png", "hcompany-agent.png", "risk-brief.png")
CREDS = {"X_CONSUMER_KEY": "k", "X_CONSUMER_KEY_SECRET": "ks",
         "X_ACCESS_TOKEN_OAUTH1": "t", "X_ACCESS_TOKEN_SECRET_OAUTH1": "ts"}


def doc(body, account="aaitor"):
    return f"---\naccount: {account}\nstatus: draft\n---\n{body}"


def write_piece(tmp_path, text, assets=()):
    (tmp_path / "x.md").write_text(text)
    (tmp_path / "assets").mkdir(exist_ok=True)
    for name in assets:
        (tmp_path / "assets" / name).write_bytes(b"\x89PNG")
    return tmp_path


@pytest.fixture
def hcompany(tmp_path):
    return write_piece(tmp_path, FIXTURE.read_text(), HCOMPANY_IMAGES)


def fake_client(username="aaitor"):
    # autospec: a wrong argument name to the real tweepy methods fails the test
    client = create_autospec(tweepy.Client, instance=True)
    client.get_me.return_value = SimpleNamespace(data=SimpleNamespace(username=username))
    client.request.side_effect = [
        Mock(**{"json.return_value": {"data": {"id": f"m{i}"}}}) for i in range(1, 9)
    ]
    client.create_tweet.side_effect = [SimpleNamespace(data={"id": f"t{i}"}) for i in range(1, 9)]
    return client


# --- x_length: 280 with every link counted as 23 -------------------------------------

def test_plain_text_counts_characters():
    assert x_length("hello world") == 11


def test_link_counts_as_23_whatever_its_length():
    long = "https://nevermined.ai/blog/x?utm_source=twitter&utm_medium=social&utm_campaign=x"
    assert x_length(long) == 23
    assert x_length("https://a.io") == 23
    assert x_length(f"see {long} and http://b.co") == 4 + 23 + 5 + 23


def test_trailing_punctuation_is_not_part_of_the_link():
    # X stops a link before closing punctuation, so it counts as text; swallowing it under-counts.
    assert x_length("(https://hcompany.ai)") == 1 + 23 + 1
    assert x_length("see https://a.io/x.") == 4 + 23 + 1
    assert x_length("https://a.io/x?y=1&z=2") == 23


def test_280_is_allowed_and_281_is_not(tmp_path):
    ok, too_long = "a" * 280, "a" * 281
    for text, errors in ((ok, 0), (too_long, 1)):
        meta, posts, images = parse(doc(text))
        assert len(check(tmp_path, meta, posts, images, "aaitor", False)) == errors


# --- parse: front matter, posts, comments ---------------------------------------------

def test_front_matter_is_read():
    meta, _, _ = parse(doc("hi", account="nevermined_ai"))
    assert meta == {"account": "nevermined_ai", "status": "draft"}


def test_missing_front_matter_is_an_error():
    with pytest.raises(ValueError, match="front matter"):
        parse("just a post")
    with pytest.raises(ValueError, match="front matter"):
        parse("---\naccount: aaitor\nno closing line")


def test_single_post_has_no_separators():
    assert parse(doc("\nOne post only.\n"))[1] == ("One post only.",)


def test_thread_splits_on_dash_lines_and_drops_empty_blocks():
    body = "\n1/ first\n\n---\n\n2/ second\n---   \n3/ third\n---\n\n---\n"
    assert parse(doc(body))[1] == ("1/ first", "2/ second", "3/ third")


def test_dashes_inside_a_line_do_not_split():
    assert parse(doc("a --- b\n-----x"))[1] == ("a --- b\n-----x",)


def test_html_comments_are_stripped_and_never_counted():
    body = "<!--\nguidance\n---\nmore\n-->\n1/ hi <!-- inline --> there\n---\n2/ bye"
    _, posts, _ = parse(doc(body))
    assert posts == ("1/ hi  there", "2/ bye")


def test_comment_only_body_has_no_posts(tmp_path):
    meta, posts, images = parse(doc("<!-- nothing to post -->"))
    assert posts == ()
    assert any("no post text" in e for e in check(tmp_path, meta, posts, images, "aaitor", False))


# --- image -> post mapping -------------------------------------------------------------

def test_hcompany_images_map_to_their_posts():
    _, posts, images = parse(FIXTURE.read_text())
    assert len(posts) == 4
    assert images == {
        1: ("assets/use-cases.png",),
        2: ("assets/hcompany-execution.png",),
        3: ("assets/hcompany-agent.png",),
        4: ("assets/risk-brief.png",),
    }
    assert not any("<!--" in p or "assets/" in p for p in posts)


def test_attach_to_post_n_wording_maps():
    text = doc("<!-- Attach image to post 1 when posting: assets/readiness-tile.png (the card) -->\nhi")
    assert parse(text)[2] == {1: ("assets/readiness-tile.png",)}


def test_several_images_on_one_post_and_case_insensitive():
    text = doc("<!-- Post 2: assets/a.PNG, assets/b.jpg and assets/c.webp -->\n1\n---\n2")
    assert parse(text)[2] == {2: ("assets/a.PNG", "assets/b.jpg", "assets/c.webp")}


def test_an_image_named_twice_for_a_post_is_attached_once():
    text = doc("<!-- post 1: assets/a.png, assets/a.png -->\n<!-- post 1: assets/a.png and assets/b.png -->\nhi")
    assert parse(text)[2] == {1: ("assets/a.png", "assets/b.png")}


def test_comment_without_images_maps_nothing():
    assert parse(doc("<!-- One post, or a thread: post 1 is the hook -->\nhi"))[2] == {}


def test_image_not_tied_to_a_post_is_an_error():
    with pytest.raises(ValueError, match="assets/lost.png"):
        parse(doc("<!-- attach assets/lost.png -->\nhi"))


def test_image_problems_are_reported(tmp_path):
    big = tmp_path / "assets" / "big.png"
    write_piece(tmp_path, "", ("ok.png",))
    big.write_bytes(b"0" * (5 * 1024 * 1024 + 1))
    (tmp_path.parent / "secret.png").write_bytes(b"x")
    images = {
        1: ("assets/ok.png",) * 5,
        2: ("assets/missing.png", "../secret.png", "assets/big.png"),
        3: ("assets/ok.png",),
        0: ("assets/ok.png",),
    }
    errors = check(tmp_path, {"account": "aaitor"}, ("a", "b"), images, "aaitor", False)
    text = "\n".join(errors)
    assert "post 1 has 5 images; X allows 4" in text
    assert "assets/missing.png is not a file" in text
    assert "../secret.png is outside" in text
    assert "assets/big.png is over 5 MB" in text
    assert "post 3" in text and "post 0" in text
    assert len(errors) == 6


def test_gif_is_rejected_not_uploaded_as_an_image(tmp_path):
    # ponytail check: animated GIFs need media_category tweet_gif (and maybe chunked upload)
    write_piece(tmp_path, "", ("anim.GIF",))
    errors = check(tmp_path, {}, ("a",), {1: ("assets/anim.GIF",)}, "aaitor", False)
    assert errors == ["assets/anim.GIF: GIFs are not supported; use PNG, JPG or WEBP"]


# --- account guard ---------------------------------------------------------------------

def test_file_account_mismatch_needs_explicit_target(tmp_path):
    meta, posts, images = parse(doc("hi", account="nevermined_ai"))
    errors = check(tmp_path, meta, posts, images, "aaitor", False)
    assert errors == ["x.md is written for @nevermined_ai, not @aaitor; pass --account aaitor to confirm"]
    assert check(tmp_path, meta, posts, images, "aaitor", True) == []


def test_matching_account_is_case_insensitive(tmp_path):
    meta, posts, images = parse(doc("hi", account="AAitor"))
    assert check(tmp_path, meta, posts, images, "aaitor", False) == []


def test_invalid_handle_is_rejected(tmp_path):
    meta, posts, images = parse(doc("hi"))
    assert check(tmp_path, meta, posts, images, "not a handle!", True) == ["@not a handle! is not a valid X handle"]


# --- publish: uploads first, then a reply chain ----------------------------------------

def test_publish_uploads_images_then_chains_replies(hcompany):
    _, posts, images = parse((hcompany / "x.md").read_text())
    client = fake_client()
    ids = publish(client, hcompany, posts, images, "aaitor")

    assert ids == ["t1", "t2", "t3", "t4"]
    order = [c[0] for c in client.mock_calls]
    assert order.index("create_tweet") > max(i for i, n in enumerate(order) if n == "request")

    uploads = client.request.call_args_list
    assert len(uploads) == 4
    for call, name in zip(uploads, HCOMPANY_IMAGES):
        assert call.args == ("POST", "/2/media/upload")
        assert call.kwargs["user_auth"] is True
        assert call.kwargs["json"] == {
            "media": base64.b64encode((hcompany / "assets" / name).read_bytes()).decode(),
            "media_category": "tweet_image",
        }

    tweets = client.create_tweet.call_args_list
    assert tweets[0].kwargs == {"text": posts[0], "media_ids": ["m1"], "in_reply_to_tweet_id": None, "user_auth": True}
    for n in (1, 2, 3):
        assert tweets[n].kwargs["in_reply_to_tweet_id"] == f"t{n}"
        assert tweets[n].kwargs["media_ids"] == [f"m{n + 1}"]


def test_publish_post_without_images_sends_no_media(tmp_path):
    client = fake_client()
    publish(client, tmp_path, ("a", "b"), {}, "aaitor")
    client.request.assert_not_called()
    assert client.create_tweet.call_args_list[1].kwargs["media_ids"] is None


def test_upload_failure_posts_nothing(hcompany):
    _, posts, images = parse((hcompany / "x.md").read_text())
    client = fake_client()
    client.request.side_effect = tweepy.TweepyException("boom")
    with pytest.raises(RuntimeError, match="nothing was posted"):
        publish(client, hcompany, posts, images, "aaitor")
    client.create_tweet.assert_not_called()


def test_failure_mid_thread_reports_what_is_live(tmp_path):
    client = fake_client()
    client.create_tweet.side_effect = [
        SimpleNamespace(data={"id": "t1"}), SimpleNamespace(data={"id": "t2"}), tweepy.TweepyException("429"),
    ]
    with pytest.raises(RuntimeError) as err:
        publish(client, tmp_path, ("a", "b", "c", "d"), {}, "aaitor")
    msg = str(err.value)
    assert "post 3 of 4 failed" in msg
    assert "https://x.com/aaitor/status/t1" in msg and "https://x.com/aaitor/status/t2" in msg


def test_response_without_an_id_still_reports_what_is_live(tmp_path):
    client = fake_client()
    client.create_tweet.side_effect = [SimpleNamespace(data={"id": "t1"}), SimpleNamespace(data=None)]
    with pytest.raises(RuntimeError) as err:
        publish(client, tmp_path, ("a", "b", "c"), {}, "aaitor")
    msg = str(err.value)
    assert "post 2 of 3 failed" in msg and "https://x.com/aaitor/status/t1" in msg
    assert "check https://x.com/aaitor" in msg


# --- credentials -----------------------------------------------------------------------

def test_missing_env_vars_are_named_not_valued():
    with pytest.raises(ValueError) as err:
        make_client({"X_CONSUMER_KEY": "secret-value"})
    msg = str(err.value)
    assert "X_CONSUMER_KEY_SECRET, X_ACCESS_TOKEN_OAUTH1, X_ACCESS_TOKEN_SECRET_OAUTH1" in msg
    assert "secret-value" not in msg


def test_oauth2_access_token_is_never_used_for_oauth1():
    # X_ACCESS_TOKEN is the OAuth 2.0 token in the credentials file; signing with it would 401.
    env = {**CREDS, "X_ACCESS_TOKEN": "oauth2"}
    del env["X_ACCESS_TOKEN_OAUTH1"]
    with pytest.raises(ValueError, match="X_ACCESS_TOKEN_OAUTH1"):
        make_client(env)


def test_client_is_built_from_env():
    with patch("tweepy.Client") as client_cls:
        make_client(CREDS)
    client_cls.assert_called_once_with(
        consumer_key="k", consumer_secret="ks", access_token="t", access_token_secret="ts"
    )


# --- main: dry run by default, --live opt-in -------------------------------------------

def test_hcompany_dry_run_needs_explicit_account(hcompany, capsys):
    factory = Mock()
    assert main([str(hcompany)], client_factory=factory) == 1
    assert "pass --account aaitor to confirm" in capsys.readouterr().err
    factory.assert_not_called()


def test_hcompany_dry_run_prints_the_thread_and_calls_nothing(hcompany, capsys):
    factory = Mock()
    assert main([str(hcompany), "--account", "@aaitor"], client_factory=factory) == 0
    out = capsys.readouterr().out
    factory.assert_not_called()
    for n, name in enumerate(HCOMPANY_IMAGES, 1):
        assert f"post {n}/4" in out and f"assets/{name}" in out
    assert "https://nevermined.ai/blog/hcompany-catalog-recall-agent" in out
    assert "Dry run: nothing posted" in out and "@aaitor" in out


def test_hcompany_posts_fit_280():
    _, posts, _ = parse(FIXTURE.read_text())
    assert all(x_length(p) <= 280 for p in posts)


def test_main_accepts_the_file_path_too(hcompany):
    assert main([str(hcompany / "x.md"), "--account", "aaitor"], client_factory=Mock()) == 0


def test_main_missing_file(tmp_path, capsys):
    assert main([str(tmp_path)]) == 1
    assert "x.md" in capsys.readouterr().err


def test_live_with_problems_never_builds_a_client(tmp_path):
    write_piece(tmp_path, doc("a" * 300))
    factory = Mock()
    assert main([str(tmp_path), "--live"], client_factory=factory) == 1
    factory.assert_not_called()


def test_live_posts_after_checking_the_account(hcompany, capsys):
    client = fake_client()
    assert main([str(hcompany), "--account", "aaitor", "--live"], client_factory=lambda: client) == 0
    assert client.mock_calls[0][0] == "get_me"
    assert client.create_tweet.call_count == 4
    assert "https://x.com/aaitor/status/t4" in capsys.readouterr().out


def test_live_refuses_credentials_for_another_account(hcompany, capsys):
    client = fake_client(username="nevermined_ai")
    assert main([str(hcompany), "--account", "aaitor", "--live"], client_factory=lambda: client) == 1
    assert "credentials are for @nevermined_ai" in capsys.readouterr().err
    client.request.assert_not_called()
    client.create_tweet.assert_not_called()


def test_live_reports_missing_credentials(hcompany, capsys, monkeypatch):
    for name in CREDS:
        monkeypatch.delenv(name, raising=False)
    assert main([str(hcompany), "--account", "aaitor", "--live"]) == 1
    err = capsys.readouterr().err
    assert "X_CONSUMER_KEY" in err and "nothing was posted" in err


def test_live_rejected_credentials_post_nothing(hcompany, capsys):
    client = fake_client()
    client.get_me.side_effect = tweepy.TweepyException("401 Unauthorized")
    assert main([str(hcompany), "--account", "aaitor", "--live"], client_factory=lambda: client) == 1
    assert "401 Unauthorized\nnothing was posted" in capsys.readouterr().err
    client.request.assert_not_called()
    client.create_tweet.assert_not_called()


def test_live_reports_a_failed_post(tmp_path, capsys):
    write_piece(tmp_path, doc("a\n---\nb"))
    client = fake_client()
    client.create_tweet.side_effect = [SimpleNamespace(data={"id": "t1"}), tweepy.TweepyException("x")]
    assert main([str(tmp_path), "--live"], client_factory=lambda: client) == 1
    assert "post 2 of 2 failed" in capsys.readouterr().err


# --- wire format: real tweepy + OAuth 1.0a signing, only the HTTP transport faked -------

def test_live_wire_requests(hcompany):
    sent = []

    def send(adapter, request, **kwargs):
        sent.append(request)
        path = request.path_url
        body = {"id": "1", "name": "A", "username": "aaitor"} if path == "/2/users/me" else {
            "id": f"{'m' if 'media' in path else 't'}{len(sent)}", "text": "x"}
        response = requests.Response()
        response.status_code, response._content, response.request = 200, json.dumps({"data": body}).encode(), request
        return response

    with patch.object(requests.adapters.HTTPAdapter, "send", send):
        assert main([str(hcompany), "--account", "aaitor", "--live"], client_factory=lambda: make_client(CREDS)) == 0

    assert [(r.method, r.path_url) for r in sent] == (
        [("GET", "/2/users/me")] + [("POST", "/2/media/upload")] * 4 + [("POST", "/2/tweets")] * 4)
    assert all(r.url.startswith("https://api.twitter.com/") for r in sent)
    assert all(r.headers["Authorization"].startswith("OAuth ") and 'oauth_consumer_key="k"' in r.headers["Authorization"]
               and 'oauth_token="t"' in r.headers["Authorization"] for r in sent)
    upload = json.loads(sent[1].body)
    assert upload["media_category"] == "tweet_image"
    assert base64.b64decode(upload["media"]) == (hcompany / "assets" / "use-cases.png").read_bytes()
    tweets = [json.loads(r.body) for r in sent[5:]]
    assert tweets[0] == {"text": parse(FIXTURE.read_text())[1][0], "media": {"media_ids": ["m2"]}}
    assert tweets[1]["reply"] == {"in_reply_to_tweet_id": "t6"}
    assert tweets[1]["media"] == {"media_ids": ["m3"]}
    assert tweets[3]["reply"] == {"in_reply_to_tweet_id": "t8"}
