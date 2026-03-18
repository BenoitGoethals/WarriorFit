-- Update all existing users' password_hash to bcrypt hash of "R@nger&1401!"
-- Hash: $2b$12$KlBTny.XeTKbJ1taCdY2M.635D3drtHB3.xjJMhBZy.YyhOwDUZzy

UPDATE users
SET password_hash = '$2b$12$KlBTny.XeTKbJ1taCdY2M.635D3drtHB3.xjJMhBZy.YyhOwDUZzy'
WHERE password_hash NOT LIKE '$2b$%';
