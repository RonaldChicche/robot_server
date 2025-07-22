function buildMethodPayload({ robot_id, name, params = {} }) {
  const timestamp = new Date().toISOString();
  const order_id = `ORD_${timestamp.replace(/[-:.TZ]/g, "")}_${name}_${robot_id}`;

  return {
    order_id,
    robot_id,
    type: "method",
    name,
    params,
    timestamp,
  };
}

function buildProcessPayload({ name, params = {} }) {
  const timestamp = new Date().toISOString();
  const order_id = `ORD_${timestamp.replace(/[-:.TZ]/g, "")}_${name}`;

  return {
    order_id,
    type: "process",
    name,
    params,
    timestamp,
  };
}

module.exports = {
  buildMethodPayload,
  buildProcessPayload,
};
