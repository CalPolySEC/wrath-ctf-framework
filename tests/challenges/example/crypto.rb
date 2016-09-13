def rot13(str)
  str.tr("a-zA-Z", "n-za-mN-ZA-M")
end
 
ARGF.each do |line|
  puts rot13(line)
end
