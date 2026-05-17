build:
	dune build

test:
	dune runtest --force

evidence:
	dune build @runtest @test/evidence --force

clean:
	dune clean
