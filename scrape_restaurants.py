import os
import luigi
from food_finder.ingest.yelp import Yelp

class CreateBusinessDictionary(luigi.Task):

	business_id = luigi.Parameter()

	def run(self):

		yelp.create_business_dictionary(self.business_id)

	def output(self):
		return luigi.LocalTarget(os.path.join(yelp.OUTPUTDIR, 'business_dicts','{0}.p'.format(self.business_id)))


class RunManyBusinesses(luigi.Task):

	def requires(self):
		for my_business_id in yelp.get_business_ids(self.term, self.location, self.radius):
			yield CreateBusinessDictionary(business_id=my_business_id)

if __name__ == "__main__":
	yelp = Yelp()
	luigi.run(main_task_cls=RunManyBusinesses)
