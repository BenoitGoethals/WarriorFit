-- Update all existing users' password_hash to Argon2id hash of "R@nger&1401!"
-- Hash: $argon2id$v=19$m=65536,t=3,p=4$0VPSG5WBx59bDno275B94Q$ahAV4VBFV4sY6HDbSO3kQ0zg8SQDkYIXkukKljoGRFA
-- Parameters: time_cost=3, memory_cost=64MB, parallelism=4

UPDATE users
SET password_hash = '$argon2id$v=19$m=65536,t=3,p=4$0VPSG5WBx59bDno275B94Q$ahAV4VBFV4sY6HDbSO3kQ0zg8SQDkYIXkukKljoGRFA'
WHERE password_hash NOT LIKE '$argon2id$%';
