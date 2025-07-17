const redis = require("redis");
const client = redis.createClient({
  url: `redis://${process.env.REDIS_HOST}:${process.env.REDIS_PORT}`,
});

client.connect();

exports.getPickAndPutFromRedis = async (robot_id) => {
  const pick = JSON.parse(await client.get(`config:${robot_id}:pick`));
  const put = JSON.parse(await client.get(`config:${robot_id}:put`));
  return { pick, put };
};
