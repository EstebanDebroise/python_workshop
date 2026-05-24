-- Active: 1777544911816@@127.0.0.1@5432@db1lab
CREATE Table Test
(
    id int,
    name varchar(255)
);

INSERT INTO Test (id, name) VALUES (1, 'Alice');
INSERT INTO Test (id, name) VALUES (2, 'Bob');

SELECT * FROM Test;

DROP TABLE Test;