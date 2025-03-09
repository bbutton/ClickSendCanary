#!/bin/bash

. $HOME/PycharmProjects/ClickSendCanary/scripts/assume_role.sh

FOLLOW_FILTER="Alert state changed|state_changed|sending notification|Email|Alert state|WARNING|CRITICAL|OK|UNKNOWN|email"

aws logs tail /aws/lambda/AthenaFailureDetectionLambda --follow | grep -E "$FOLLOW_FILTER"
