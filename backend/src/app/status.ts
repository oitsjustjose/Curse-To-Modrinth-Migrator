enum Status {
  ENQUEUED = 0,
  PROCESSING = 1,
  COMPLETE = 2,
  SUCCESS = 3,
  PARTIAL_FAIL = 4,
  FAIL = 5,
  NOTFOUND = -1,
}

export default Status;
