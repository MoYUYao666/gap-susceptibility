#!/bin/bash
set -e
cd /root/autodl-tmp/a3
tar czf cloud_runs.tgz runs/cloud_l14 runs/cloud_fullcorpus runs/cloud_fullextra runs/cloud_l14_nwpu
ls -lh cloud_runs.tgz
sha256sum cloud_runs.tgz
echo FETCH_READY
