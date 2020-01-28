CREATE TYPE vote AS ENUM ('upvote', 'downvote');

CREATE TABLE IF NOT EXISTS karma (
    id SERIAL PRIMARY KEY,
    time_given TIMESTAMP NOT NULL DEFAULT now(),
    message_id BIGINT NOT NULL,
    karma_type vote NOT NULL,
    giver BIGINT NOT NULL,
    receiver BIGINT NOT NULL
);


CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    role_id BIGINT NOT NULL,
    role_name TEXT NOT NULL
);


CREATE FUNCTION get_karma(BIGINT) RETURNS BIGINT AS $$
    SELECT (SELECT COUNT(*) FROM karma WHERE receiver=$1 AND karma_type='upvote') -
    (SELECT COUNT(*) FROM karma WHERE receiver=$1 AND karma_type='downvote');
$$ LANGUAGE SQL;