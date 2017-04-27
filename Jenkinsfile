#!/usr/bin/env groovy

REPOSITORY = 'stagecraft'

node {
	def govuk = load '/var/lib/jenkins/groovy_scripts/govuk_jenkinslib.groovy'

	try {
		stage('Checkout') {
			govuk.checkoutFromGitHubWithSSH(REPOSITORY)
		}

		stage('Clean') {
			govuk.cleanupGit()
			govuk.mergeMasterBranch()
		}

		stage('Build') {
			sh("rm -rf ./venv")
			sh("virtualenv --no-site-packages ./venv")
			sh("./venv/bin/python ./venv/bin/pip install --upgrade pip wheel")
			sh("./venv/bin/python ./venv/bin/pip install -r requirements/ci.txt")
		}

		stage('Test') {
			govuk.setEnvar("DJANGO_SETTINGS_MODULE", "stagecraft.settings.ci")
			govuk.setEnvar("DATABASE_URL", "postgres://jenkins:jenkins@localhost:5432/postgres")
			govuk.setEnvar("SECRET_KEY", "xyz")
			govuk.setEnvar("NO_AUTOPEP8", "1")
			sh("./venv/bin/python manage.py test -v 2 --with-coverage --with-doctest stagecraft/")
		}

		if (env.BRANCH_NAME == 'master') {
			stage('Push release tag') {
				govuk.pushTag(REPOSITORY, BRANCH_NAME, 'release_' + BUILD_NUMBER)
			}
			stage('Deploy to Integration') {
				govuk.deployIntegration(REPOSITORY, BRANCH_NAME, 'release', 'deploy')
			}
		}
	} catch (e) {
		currentBuild.result = 'FAILED'
		step([$class                  : 'Mailer',
			  notifyEveryUnstableBuild: true,
			  recipients              : 'govuk-ci-notifications@digital.cabinet-office.gov.uk',
			  sendToIndividuals       : true])
		throw e
	}

	// Wipe the workspace
	deleteDir()
}
