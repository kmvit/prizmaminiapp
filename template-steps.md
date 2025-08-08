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



UPDATE users
SET
  is_paid = 0,
  is_premium_paid = 0,
  test_completed = 0,
  current_question_id = NULL,
  test_started_at = NULL,
  test_completed_at = NULL,
  free_report_status = 'PENDING',
  premium_report_status = 'PENDING',
  free_report_path = NULL,
  premium_report_path = NULL,
  report_generation_error = NULL,
  report_generation_started_at = NULL,
  report_generation_completed_at = NULL,
  updated_at = CURRENT_TIMESTAMP;

DELETE FROM reports;
DELETE FROM answers;
DELETE FROM payments;

COMMIT;

-- Контроль
SELECT COUNT(*) AS total_users FROM users;
SELECT COUNT(*) AS paid_users FROM users WHERE is_paid = 1;
SELECT COUNT(*) AS premium_paid_users FROM users WHERE is_premium_paid = 1;
SELECT COUNT(*) AS completed_tests FROM users WHERE test_completed = 1;