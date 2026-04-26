// export const filterDataByRange = (data: DataPoint[], range: TimeRange) => {
//   const now = Date.now();

//   const ranges = {
//     day: 24 * 60 * 60 * 1000,
//     week: 7 * 24 * 60 * 60 * 1000,
//     month: 30 * 24 * 60 * 60 * 1000,
//   };

//   return data.filter((d) => now - d.timestamp <= ranges[range]);
// };