BEGIN {
	print("ACCX,ACCY,ACCZ,GYRX,GYRY,GYRZ")
}
{
	gsub(/(^acc: \(|\)$)/,"")
	gsub("\), gyro; \(", ",")
	print($0)
}
