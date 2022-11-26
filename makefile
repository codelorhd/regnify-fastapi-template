
# ****************** DIRECT DEVELOPMENT ****************** #

start-uvicorn:
	uvicorn src.main:app --reload --port 8100

start-dev-postgres:
	docker-compose -f ./docker/local/compose-files/docker-compose-postgres.yml up

# ****************** END DIRECT DEVELOPMENT ****************** #

# -- 
# -- 
# -- 

# ****************** ALEMBIC ****************** #

run-db-upgrade:
	alembic upgrade head

# ****************** END ALEMBIC ****************** #



# -- 
# -- 
# -- 


# ****************** TESTS ****************** #

build-local:
	docker compose -f docker/local/docker-compose.yml build 

kill-local:
	docker compose -f docker/local/docker-compose.yml down

run-local-migrations:
	docker compose -f docker/local/docker-compose.yml run -v ${PWD}:/usr/src/regnify-api  --rm regnify-api  alembic upgrade head

make init-platform:
	docker compose -f docker/local/docker-compose.yml run -v ${PWD}:/usr/src/regnify-api --rm regnify-api python ./src/init_platform.py

run:
	make run-local-migrations

	make make init-platform

	docker compose -f docker/local/docker-compose.yml up  --remove-orphans  -d

restart:
	docker compose -f docker/local/docker-compose.yml down regnify-api
	make run


follow-logs:
	docker compose -f docker/local/docker-compose.yml logs regnify-api -f


# ****************** END TESTS ****************** #

# -- 
# -- 
# -- 

# ****************** TESTS ****************** #

build-test:
	docker compose -f docker/test/docker-compose-test.yml build 

kill-test: kill-local
	docker compose -f docker/test/docker-compose-test.yml down

run-test-migrations:
	docker compose -f docker/test/docker-compose-test.yml run -v ${PWD}:/usr/src/regnify-api  --rm regnify-api alembic upgrade head


# * ------ User Module ------ * #

# Runs all tests under the user modules
run-test-users:
	make kill-test

	make run-test-migrations

	# * run the tests
	docker compose -f docker/test/docker-compose-test.yml run -v ${PWD}:/usr/src/regnify-api  --rm regnify-api python -m pytest --cov=src/users tests/users

	make kill-test

run-test-users-crud:
	make kill-test

	make run-test-migrations
	
	# * run the tests
	docker compose -f docker/test/docker-compose-test.yml run -v ${PWD}:/usr/src/regnify-api  --rm regnify-api python -m pytest --cov=src/users tests/users/crud

	make kill-test

run-test-users-services:
	make kill-test

	make run-test-migrations
	
	# * run the tests
	docker compose -f docker/test/docker-compose-test.yml run -v ${PWD}:/usr/src/regnify-api --rm regnify-api python -m pytest --cov=src/users tests/users/services/

	make kill-test

run-test-users-http:
	make kill-test

	make run-test-migrations
	
	# * run the tests
	docker compose -f docker/test/docker-compose-test.yml run -v ${PWD}:/usr/src/regnify-api --rm regnify-api python -m pytest --cov=src/users tests/users/http/

	make kill-test

# * ------ End User Modules ------ * #

# ****************** END TESTS ****************** #

# -- 
# -- 
# -- 

# ****************** MISC ****************** #

create-network:
	docker network create regnify-network

# ****************** END MISC ****************** #