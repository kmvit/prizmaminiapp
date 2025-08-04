1.index.html
2.steps.html 
3.price.html
4.login.html
5.question.html
6.loading.html


Скачивание бесплатной расшифровки price-offer.html
Скачивание полной расшифровки download.html
Оплата прошла complete-payment.html
Оплата не прошла uncomplete-payment.html
FAQ answers.html


-- Обнуляем статус оплаты у всех пользователей
UPDATE users SET is_paid = 0;

-- Обнуляем премиум оплату у всех пользователей
UPDATE users SET is_premium_paid = 0;

-- Обнуляем завершение теста у всех пользователей  
UPDATE users SET test_completed = 0;

-- Обнуляем текущий вопрос у всех пользователей
UPDATE users SET current_question_id = NULL;

-- Удаляем все отчеты
DELETE FROM reports;

-- Удаляем все ответы пользователей
DELETE FROM answers;

-- Удаляем все платежи
DELETE FROM payments;

-- Проверяем результат
SELECT 'Пользователи сброшены:' as status;
SELECT COUNT(*) as total_users FROM users;
SELECT COUNT(*) as paid_users FROM users WHERE is_paid = 1;
SELECT COUNT(*) as premium_paid_users FROM users WHERE is_premium_paid = 1;
SELECT COUNT(*) as completed_tests FROM users WHERE test_completed = 1;